"""
Pure evaluation functions: validate one MCQ row, call the judge, map the
judge's JSON back to typed RowResult objects.

Each function is independently testable with a mocked judge.
"""

import logging
from typing import Optional

import pandas as pd

from evaluation.models import CheckResult, EvalReport, RowResult, Verdict
from evaluation.judge_prompts import get_combined_judge_prompt
from evaluation.llm_judge import LLMJudge

logger = logging.getLogger(__name__)

# Minimum length for a field to be considered non-empty
_MIN_LEN = 3


def _str(val) -> str:
    """Coerce a pandas cell to a clean string; treat NaN/None as empty."""
    if val is None:
        return ""
    if isinstance(val, float) and pd.isna(val):
        return ""
    return str(val).strip()


def validate_row_input(row: dict) -> tuple[bool, str]:
    """
    Check whether a KB row has the required fields to be judged.

    Returns (is_valid, reason).  Rows that are invalid are tagged
    INVALID_INPUT and never sent to the LLM.
    """
    q = _str(row.get("Question_Text"))
    if len(q) < _MIN_LEN:
        return False, "Question_Text missing or too short"

    for opt in ("Option_A", "Option_B", "Option_C", "Option_D"):
        if len(_str(row.get(opt))) < _MIN_LEN:
            return False, f"{opt} missing or too short"

    return True, ""


def make_invalid_result(row: dict, reason: str) -> RowResult:
    """Build an INVALID_INPUT RowResult without touching the LLM."""
    return RowResult(
        question_id=_str(row.get("Question_ID", "unknown")),
        question_text=_str(row.get("Question_Text")),
        stored_answer=_str(row.get("Correct_Answer")) or None,
        llm_answer=None,
        answerable=CheckResult.NA,
        answer_match=CheckResult.NA,
        explanation_consistent=CheckResult.NA,
        verdict=Verdict.INVALID_INPUT,
        confidence=0.0,
        rationale=f"Input validation failed: {reason}",
    )


def make_error_result(row: dict, reason: str) -> RowResult:
    """Build an ERROR RowResult when the LLM call or parse step fails."""
    return RowResult(
        question_id=_str(row.get("Question_ID", "unknown")),
        question_text=_str(row.get("Question_Text")),
        stored_answer=_str(row.get("Correct_Answer")) or None,
        llm_answer=None,
        answerable=CheckResult.NA,
        answer_match=CheckResult.NA,
        explanation_consistent=CheckResult.NA,
        verdict=Verdict.ERROR,
        confidence=0.0,
        rationale=f"Judging failed: {reason}",
    )


def map_check(value: str) -> CheckResult:
    """Map a raw string from the judge JSON to a typed CheckResult."""
    v = value.strip().upper() if value else ""
    if v == "PASS":
        return CheckResult.PASS
    if v == "FAIL":
        return CheckResult.FAIL
    return CheckResult.NA


def determine_verdict(
    answerable: CheckResult,
    answer_match: CheckResult,
    explanation_consistent: CheckResult,
) -> Verdict:
    """
    Gate logic for the overall verdict.

    Order matters — later checks are only meaningful if earlier ones pass:
    1. Not answerable → NOT_ANSWERABLE (skip other checks)
    2. Answer mismatch → WRONG_ANSWER (skip explanation check)
    3. Explanation inconsistent → BAD_EXPLANATION
    4. All pass → PASS
    """
    if answerable == CheckResult.FAIL:
        return Verdict.NOT_ANSWERABLE
    if answer_match == CheckResult.FAIL:
        return Verdict.WRONG_ANSWER
    if explanation_consistent == CheckResult.FAIL:
        return Verdict.BAD_EXPLANATION
    return Verdict.PASS


async def judge_row(row: dict, judge: LLMJudge) -> RowResult:
    """
    Evaluate a single KB row (as a dict from DataFrame.iterrows).

    Returns a fully populated RowResult regardless of outcome.
    """
    question_id = _str(row.get("Question_ID", "unknown"))
    question_text = _str(row.get("Question_Text"))
    option_a = _str(row.get("Option_A"))
    option_b = _str(row.get("Option_B"))
    option_c = _str(row.get("Option_C"))
    option_d = _str(row.get("Option_D"))
    explanation = _str(row.get("Explanation")) or None
    stored_answer = _str(row.get("Correct_Answer")).upper() or None
    if stored_answer and stored_answer not in ("A", "B", "C", "D"):
        stored_answer = None

    # Step 1: validate input — no LLM call needed for invalid rows
    is_valid, reason = validate_row_input(row)
    if not is_valid:
        logger.debug(f"[{question_id[:8]}] INVALID_INPUT: {reason}")
        return make_invalid_result(row, reason)

    # Step 2: build prompt and call judge
    prompt = get_combined_judge_prompt(
        question_text=question_text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        explanation=explanation,
        stored_answer=stored_answer,
    )

    raw = await judge.judge(prompt)
    if not raw:
        logger.warning(f"[{question_id[:8]}] Judge returned no response")
        return make_error_result(row, "No response from LLM judge")

    parsed = judge.parse_response(raw)
    if not parsed:
        logger.warning(f"[{question_id[:8]}] Could not parse judge JSON")
        return make_error_result(row, "Failed to parse judge response as JSON")

    # Step 3: map parsed fields to typed enums
    answerable = map_check(parsed.get("answerable", ""))
    llm_answer_raw = _str(parsed.get("llm_answer", "")).upper()
    llm_answer: Optional[str] = llm_answer_raw if llm_answer_raw in ("A", "B", "C", "D") else None
    answer_match = map_check(parsed.get("answer_match", ""))
    explanation_consistent = map_check(parsed.get("explanation_consistent", ""))
    confidence = float(parsed.get("confidence", 0.5))
    rationale = _str(parsed.get("rationale", "No rationale provided"))

    # Step 4: derive overall verdict
    verdict = determine_verdict(answerable, answer_match, explanation_consistent)

    logger.debug(
        f"[{question_id[:8]}] stored={stored_answer} llm={llm_answer} "
        f"match={answer_match.value} verdict={verdict.value}"
    )

    return RowResult(
        question_id=question_id,
        question_text=question_text,
        stored_answer=stored_answer,
        llm_answer=llm_answer,
        answerable=answerable,
        answer_match=answer_match,
        explanation_consistent=explanation_consistent,
        verdict=verdict,
        confidence=confidence,
        rationale=rationale,
    )


def accumulate(report: EvalReport, result: RowResult) -> None:
    """Update aggregate counters on report in-place after each row is judged."""
    report.judged += 1
    report.results.append(result)

    v = result.verdict
    if v == Verdict.PASS:
        report.passed += 1
    elif v == Verdict.WRONG_ANSWER:
        report.wrong_answer += 1
        # Track which letter was stored vs what LLM picked
        if result.stored_answer and result.llm_answer:
            key = f"{result.stored_answer}->{result.llm_answer}"
            report.disagreement_map[key] = report.disagreement_map.get(key, 0) + 1
    elif v == Verdict.BAD_EXPLANATION:
        report.bad_explanation += 1
    elif v == Verdict.NOT_ANSWERABLE:
        report.not_answerable += 1
    elif v == Verdict.INVALID_INPUT:
        report.invalid_input += 1
    elif v == Verdict.ERROR:
        report.errors += 1

    # Track data-quality observation independently
    row_dict = result.__dict__
    if result.explanation_consistent == CheckResult.NA and result.verdict not in (
        Verdict.INVALID_INPUT,
        Verdict.ERROR,
        Verdict.NOT_ANSWERABLE,
    ):
        report.missing_explanation += 1
