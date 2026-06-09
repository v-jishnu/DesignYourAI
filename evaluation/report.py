"""
Report writers: annotated Excel, JSON summary, and console output.

The annotated Excel is the primary deliverable: the original KB columns are
preserved exactly, and seven Eval_* columns are appended so the client can
sort by Eval_Verdict to jump straight to failures.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from evaluation.models import EvalReport, Verdict

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Console summary
# ------------------------------------------------------------------

def print_summary(report: EvalReport) -> None:
    """Print a clean summary block to stdout."""
    sep = "=" * 70
    print(f"\n{sep}")
    print("MCQ EVALUATION REPORT")
    print(sep)
    print(f"  Source:   {report.excel_path}")
    print(f"  Provider: {report.provider} / {report.model}")
    print(f"  Total rows in KB:         {report.total_rows}")
    print(f"  Rows judged:              {report.judged}")
    print(f"  Invalid input (skipped):  {report.invalid_input}")
    print(f"  Judge errors (skipped):   {report.errors}")
    print(f"  Answerable rows:          {report.answerable_rows}")
    print()
    print(f"  PASS:                     {report.passed}")
    print(f"  WRONG_ANSWER:             {report.wrong_answer}  <- stored answer != LLM pick")
    print(f"  BAD_EXPLANATION:          {report.bad_explanation}  <- answer ok, explanation mismatch")
    print(f"  NOT_ANSWERABLE:           {report.not_answerable}  <- options degenerate/ambiguous")
    print(f"  Missing explanation (N/A):{report.missing_explanation}")
    print()
    print(f"  Pass rate (of answerable): {report.pass_rate*100:.1f}%")
    print(f"  Wrong-answer rate:         {report.wrong_answer_rate*100:.1f}%")

    if report.disagreement_map:
        print()
        print("  Disagreement breakdown (stored->LLM):")
        for key, count in sorted(report.disagreement_map.items(), key=lambda x: -x[1]):
            print(f"    {key}: {count}")

    print(sep + "\n")


# ------------------------------------------------------------------
# Annotated Excel
# ------------------------------------------------------------------

def write_annotated_excel(report: EvalReport, output_path: Path) -> None:
    """
    Write an annotated copy of the original KB with Eval_* columns appended.

    The original KB is loaded fresh from report.excel_path so we don't rely on
    any in-memory state. Then we join the eval results by Question_ID.
    """
    try:
        df = pd.read_excel(report.excel_path)
    except Exception as exc:
        logger.error(f"Could not load original Excel for annotation: {exc}")
        return

    # Build a lookup: question_id -> eval row dict
    eval_lookup = {r.question_id: r.to_row() for r in report.results}

    eval_cols = [
        "Eval_Answerable",
        "Eval_LLM_Answer",
        "Eval_Answer_Match",
        "Eval_Explanation_Consistent",
        "Eval_Verdict",
        "Eval_Confidence",
        "Eval_Rationale",
    ]

    # Add eval columns to DataFrame
    for col in eval_cols:
        df[col] = None

    for idx, row in df.iterrows():
        qid = str(row.get("Question_ID", "")).strip()
        if qid in eval_lookup:
            for col, val in eval_lookup[qid].items():
                df.at[idx, col] = val

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(output_path, index=False)
        logger.info(f"Annotated Excel written to {output_path}")
    except Exception as exc:
        logger.error(f"Failed to write annotated Excel: {exc}")


# ------------------------------------------------------------------
# JSON report
# ------------------------------------------------------------------

def write_json_report(report: EvalReport, output_path: Path) -> None:
    """Write the full EvalReport to a JSON file for trend tracking."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"JSON report written to {output_path}")
    except Exception as exc:
        logger.error(f"Failed to write JSON report: {exc}")


# ------------------------------------------------------------------
# Convenience: write both outputs
# ------------------------------------------------------------------

def write_all(report: EvalReport, excel_out: Optional[Path] = None, json_out: Optional[Path] = None) -> None:
    """Write annotated Excel + JSON report, then print console summary."""
    source = Path(report.excel_path)

    if excel_out is None:
        excel_out = source.parent / (source.stem + "_eval.xlsx")
    if json_out is None:
        json_out = source.parent / (source.stem + "_eval.json")

    print_summary(report)
    write_annotated_excel(report, excel_out)
    write_json_report(report, json_out)

    print(f"  Annotated KB: {excel_out}")
    print(f"  JSON report:  {json_out}\n")
