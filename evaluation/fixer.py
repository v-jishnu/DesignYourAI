"""
MCQ Fixer: patches Correct_Answer and Explanation for flagged rows.

Rules:
- WRONG_ANSWER  → set Correct_Answer = LLM's blind pick, regenerate Explanation
- BAD_EXPLANATION → keep Correct_Answer, regenerate Explanation only
- NOT_ANSWERABLE → drop the row (options are unfixable; question is bad)
- PASS / INVALID_INPUT / ERROR → copy through unchanged

The question text and all four options are NEVER modified. Only
Correct_Answer and Explanation can change.
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Optional

import pandas as pd

from evaluation.fix_prompts import get_fix_wrong_answer_prompt, get_fix_bad_explanation_prompt
from evaluation.llm_judge import LLMJudge
from evaluation.models import EvalReport, Verdict

logger = logging.getLogger(__name__)


def _str(val) -> str:
    if val is None:
        return ""
    if isinstance(val, float) and pd.isna(val):
        return ""
    return str(val).strip()


class MCQFixer:
    """Fix flagged MCQ rows using a targeted LLM repair prompt."""

    def __init__(self, judge: LLMJudge, concurrency: int = 2):
        self.judge = judge
        self.concurrency = concurrency

    async def fix_dataframe(
        self,
        df: pd.DataFrame,
        report: EvalReport,
        verbose: bool = False,
    ) -> tuple[pd.DataFrame, dict]:
        """
        Apply fixes to all flagged rows in the DataFrame.

        Args:
            df: The original KB DataFrame (must have Question_ID column).
            report: The EvalReport produced by EvaluationPipeline.run().
            verbose: Print per-row fix status.

        Returns:
            (fixed_df, stats) where fixed_df has corrected Correct_Answer and
            Explanation columns, and stats summarises what was done.
        """
        # Build lookup: question_id -> RowResult
        result_map = {r.question_id: r for r in report.results}

        stats = {
            "total_rows": len(df),
            "passed_unchanged": 0,
            "wrong_answer_fixed": 0,
            "bad_explanation_fixed": 0,
            "not_answerable_dropped": 0,
            "invalid_kept": 0,
            "error_kept": 0,
            "fix_failed": 0,
        }

        # Collect rows that need async LLM calls
        rows_needing_fix = []
        for idx, row in df.iterrows():
            qid = _str(row.get("Question_ID"))
            result = result_map.get(qid)
            if result and result.verdict in (Verdict.WRONG_ANSWER, Verdict.BAD_EXPLANATION):
                rows_needing_fix.append((idx, row, result))

        logger.info(f"Rows needing LLM fix: {len(rows_needing_fix)}")

        # Run fixes concurrently
        sem = asyncio.Semaphore(self.concurrency)
        fix_results: dict = {}  # idx -> {"correct_answer": ..., "explanation": ...} or None

        async def _fix_one(idx, row, result):
            async with sem:
                patch = await self._fix_row(row, result)
            fix_results[idx] = patch
            if verbose:
                status = "fixed" if patch else "FAILED"
                line = (
                    f"  [fix] {status:6s}  {result.verdict.value:18s}  "
                    f"{_str(row.get('Question_Text'))[:60]}..."
                )
                print(line.encode("ascii", errors="replace").decode("ascii"))

        tasks = [
            asyncio.create_task(_fix_one(idx, row, result))
            for idx, row, result in rows_needing_fix
        ]
        await asyncio.gather(*tasks)

        # Build output DataFrame: iterate original, apply patches, drop NOT_ANSWERABLE
        keep_rows = []
        for idx, row in df.iterrows():
            qid = _str(row.get("Question_ID"))
            result = result_map.get(qid)

            if result is None:
                # Row was not in the eval scope (e.g. not sampled) — keep as-is
                keep_rows.append(row.to_dict())
                stats["passed_unchanged"] += 1
                continue

            verdict = result.verdict

            if verdict == Verdict.NOT_ANSWERABLE:
                stats["not_answerable_dropped"] += 1
                continue  # drop

            if verdict == Verdict.PASS:
                keep_rows.append(row.to_dict())
                stats["passed_unchanged"] += 1
                continue

            if verdict == Verdict.INVALID_INPUT:
                keep_rows.append(row.to_dict())
                stats["invalid_kept"] += 1
                continue

            if verdict == Verdict.ERROR:
                keep_rows.append(row.to_dict())
                stats["error_kept"] += 1
                continue

            # WRONG_ANSWER or BAD_EXPLANATION — apply patch
            patch = fix_results.get(idx)
            if patch:
                row_dict = row.to_dict()
                row_dict["Correct_Answer"] = patch["correct_answer"]
                row_dict["Explanation"] = patch["explanation"]
                keep_rows.append(row_dict)
                if verdict == Verdict.WRONG_ANSWER:
                    stats["wrong_answer_fixed"] += 1
                else:
                    stats["bad_explanation_fixed"] += 1
            else:
                # Fix call failed — keep original row rather than silently corrupt
                keep_rows.append(row.to_dict())
                stats["fix_failed"] += 1
                logger.warning(f"Fix failed for {qid[:8] if qid else 'unknown'}, keeping original")

        fixed_df = pd.DataFrame(keep_rows)
        return fixed_df, stats

    async def _fix_row(self, row, result) -> Optional[dict]:
        """
        Call the LLM with the appropriate fix prompt and parse the response.
        Returns {"correct_answer": "X", "explanation": "..."} or None on failure.
        """
        question_text = _str(row.get("Question_Text"))
        option_a = _str(row.get("Option_A"))
        option_b = _str(row.get("Option_B"))
        option_c = _str(row.get("Option_C"))
        option_d = _str(row.get("Option_D"))

        if result.verdict == Verdict.WRONG_ANSWER:
            correct_letter = result.llm_answer  # evaluator's blind pick is the correct one
            if not correct_letter:
                logger.warning("WRONG_ANSWER row has no llm_answer, skipping fix")
                return None
            prompt = get_fix_wrong_answer_prompt(
                question_text, option_a, option_b, option_c, option_d, correct_letter
            )
        else:  # BAD_EXPLANATION
            correct_letter = result.stored_answer  # answer is right, just fix explanation
            if not correct_letter:
                logger.warning("BAD_EXPLANATION row has no stored_answer, skipping fix")
                return None
            prompt = get_fix_bad_explanation_prompt(
                question_text, option_a, option_b, option_c, option_d, correct_letter
            )

        raw = await self.judge.judge(prompt)
        if not raw:
            return None

        return self._parse_fix_response(raw, correct_letter)

    def _parse_fix_response(self, raw: str, expected_letter: str) -> Optional[dict]:
        """Parse the fixer's JSON response."""
        text = raw.strip()

        # Strip markdown fences
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text.rstrip())
            text = text.strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            logger.error(f"No JSON object in fix response: {raw[:200]}")
            return None

        text = text[start:end + 1]

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            text = re.sub(r",\s*\}", "}", text)
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse fix JSON: {text[:200]}")
                return None

        correct_answer = _str(data.get("correct_answer", "")).upper()
        explanation = _str(data.get("explanation", ""))

        # Sanity check: correct_answer must be a valid letter
        if correct_answer not in ("A", "B", "C", "D"):
            logger.warning(f"Fix response has invalid correct_answer '{correct_answer}', using expected {expected_letter}")
            correct_answer = expected_letter

        if not explanation or len(explanation) < 20:
            logger.warning("Fix response has empty/short explanation")
            return None

        return {"correct_answer": correct_answer, "explanation": explanation}
