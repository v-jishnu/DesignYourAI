"""
EvaluationPipeline: loads an Excel KB, judges every row asynchronously,
aggregates results into an EvalReport, and writes a resumable cache.

Key design decisions:
- asyncio.Semaphore(concurrency) throttles Ollama (default 2; raise for API providers)
- A JSONL cache (one verdict per line keyed by Question_ID) lets a re-run skip
  already-judged rows, so a slow local run can be interrupted safely.
- Rows missing options are tagged INVALID_INPUT immediately without an LLM call.
- Rows missing explanation still get checks 1-3; check 4 comes back N/A.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd

from evaluation.evaluators import accumulate, judge_row
from evaluation.llm_judge import LLMJudge, build_judge_client
from evaluation.models import EvalReport, RowResult, Verdict

logger = logging.getLogger(__name__)


class EvaluationPipeline:
    """Orchestrate end-to-end evaluation of an MCQ knowledge-base Excel file."""

    def __init__(
        self,
        config: dict,
        concurrency: int = 2,
        cache_path: Optional[Path] = None,
    ):
        """
        Args:
            config: The same config dict produced by Settings.get_config().
            concurrency: Max concurrent LLM calls.  Keep at 2 for local Ollama
                         to avoid OOM; raise to 8-16 for API providers.
            cache_path: Path to a .jsonl file for resumable caching.
                        Defaults to <excel_stem>_eval_cache.jsonl next to the Excel.
        """
        self.config = config
        self.concurrency = concurrency
        self.cache_path = cache_path
        self._client = build_judge_client(config)
        self._judge = LLMJudge(self._client)
        llm_config = config.get("llm_config", {})
        self._provider = llm_config.get("provider", "ollama")
        self._model = llm_config.get("model", "unknown")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def run(
        self,
        excel_path: Path,
        limit: Optional[int] = None,
        sample: Optional[float] = None,
        verbose: bool = False,
    ) -> EvalReport:
        """
        Evaluate all (or a subset of) rows in the Excel KB.

        Args:
            excel_path: Path to the .xlsx file to evaluate.
            limit: If set, only judge the first N rows.
            sample: If set (0 < sample <= 1), randomly sample that fraction.
            verbose: Print per-row progress to stdout.

        Returns:
            A fully populated EvalReport.
        """
        df = self._load_excel(excel_path)

        if sample and 0 < sample < 1:
            df = df.sample(frac=sample, random_state=42)
            logger.info(f"Sampled {len(df)} rows ({sample*100:.0f}%)")

        if limit:
            df = df.head(limit)
            logger.info(f"Limiting to first {limit} rows")

        report = EvalReport(
            excel_path=str(excel_path),
            provider=self._provider,
            model=self._model,
            total_rows=len(df),
        )

        # Resolve cache path
        cache_path = self.cache_path or excel_path.parent / (excel_path.stem + "_eval_cache.jsonl")
        already_judged = self._load_cache(cache_path)
        logger.info(f"Cache: {len(already_judged)} rows already judged (will skip)")

        rows = list(df.iterrows())
        sem = asyncio.Semaphore(self.concurrency)

        async def _judge_with_semaphore(idx: int, row_series) -> RowResult:
            row = row_series.to_dict()
            qid = str(row.get("Question_ID", "")).strip()

            # Resume: return cached result without calling LLM
            if qid and qid in already_judged:
                logger.debug(f"[{qid[:8]}] cache hit, skipping")
                return already_judged[qid]

            async with sem:
                result = await judge_row(row, self._judge)

            # Persist to cache immediately so a crash loses at most this row
            self._append_cache(cache_path, result)

            if verbose:
                line = (
                    f"  [{idx+1}/{len(rows)}] {result.verdict.value:18s} "
                    f"stored={result.stored_answer or '?'} "
                    f"llm={result.llm_answer or '?'} "
                    f"conf={result.confidence:.2f}  "
                    f"{result.question_text[:60]}..."
                )
                print(line.encode("ascii", errors="replace").decode("ascii"))

            return result

        tasks = [
            asyncio.create_task(_judge_with_semaphore(i, row))
            for i, (_, row) in enumerate(rows)
        ]

        results: List[RowResult] = await asyncio.gather(*tasks)

        for result in results:
            accumulate(report, result)

        return report

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_excel(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(f"Excel KB not found: {path}")
        df = pd.read_excel(path)
        logger.info(f"Loaded {len(df)} rows from {path.name}")
        return df

    def _load_cache(self, cache_path: Path) -> dict:
        """Load previously judged results from the JSONL cache."""
        if not cache_path.exists():
            return {}

        judged: dict = {}
        try:
            with open(cache_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        qid = d.get("question_id")
                        if qid:
                            judged[qid] = self._dict_to_row_result(d)
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception as exc:
            logger.warning(f"Could not read cache {cache_path}: {exc}")

        return judged

    def _append_cache(self, cache_path: Path, result: RowResult) -> None:
        """Append a single RowResult to the JSONL cache."""
        try:
            with open(cache_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(result.to_dict()) + "\n")
        except Exception as exc:
            logger.warning(f"Cache write failed: {exc}")

    @staticmethod
    def _dict_to_row_result(d: dict) -> RowResult:
        """Reconstruct a RowResult from a cached dict (reverse of to_dict)."""
        from evaluation.models import CheckResult, Verdict

        def _cr(v: str) -> CheckResult:
            return CheckResult(v) if v in ("PASS", "FAIL", "N/A") else CheckResult.NA

        return RowResult(
            question_id=d.get("question_id", ""),
            question_text=d.get("question_text", ""),
            stored_answer=d.get("stored_answer"),
            llm_answer=d.get("llm_answer"),
            answerable=_cr(d.get("answerable", "N/A")),
            answer_match=_cr(d.get("answer_match", "N/A")),
            explanation_consistent=_cr(d.get("explanation_consistent", "N/A")),
            verdict=Verdict(d.get("verdict", "ERROR")),
            confidence=float(d.get("confidence", 0.0)),
            rationale=d.get("rationale", ""),
        )
