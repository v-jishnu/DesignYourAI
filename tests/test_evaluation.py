"""
Unit tests for the evaluation pipeline.

These tests use a mocked LLMJudge so no live LLM call is made.  They validate:
- Input validation (invalid rows caught before any LLM call)
- Verdict gate logic (determine_verdict precedence)
- JSON response parsing (including malformed JSON)
- Accumulator (EvalReport counters)
- Full judge_row integration with a mock

Run with:  python -m pytest tests/test_evaluation.py -v
"""

import asyncio
import pytest

from evaluation.models import CheckResult, EvalReport, RowResult, Verdict
from evaluation.evaluators import (
    accumulate,
    determine_verdict,
    make_invalid_result,
    validate_row_input,
    judge_row,
    map_check,
)
from evaluation.llm_judge import LLMJudge


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

def _good_row(**overrides) -> dict:
    base = {
        "Question_ID": "test-qid-001",
        "Question_Text": "Which activation function is commonly used in the output layer for multi-class classification?",
        "Option_A": "ReLU",
        "Option_B": "Sigmoid",
        "Option_C": "Softmax",
        "Option_D": "Tanh",
        "Correct_Answer": "C",
        "Explanation": "Softmax converts raw logits into a probability distribution across classes, making it the standard choice for multi-class classification output layers.",
    }
    base.update(overrides)
    return base


class MockJudge(LLMJudge):
    """Judge that returns a pre-set raw JSON string without calling any LLM."""

    def __init__(self, raw_response: str):
        self._raw = raw_response

    async def judge(self, prompt: str) -> str:
        return self._raw

    def parse_response(self, raw: str) -> dict | None:
        return super().parse_response(raw)  # use real parser


# ------------------------------------------------------------------
# validate_row_input
# ------------------------------------------------------------------

class TestValidateRowInput:
    def test_good_row_passes(self):
        valid, reason = validate_row_input(_good_row())
        assert valid is True
        assert reason == ""

    def test_missing_question_fails(self):
        valid, reason = validate_row_input(_good_row(Question_Text=""))
        assert valid is False
        assert "Question_Text" in reason

    def test_missing_option_fails(self):
        valid, reason = validate_row_input(_good_row(Option_B="  "))
        assert valid is False
        assert "Option_B" in reason

    def test_nan_option_fails(self):
        import math
        valid, reason = validate_row_input(_good_row(Option_C=math.nan))
        assert valid is False

    def test_short_option_fails(self):
        valid, reason = validate_row_input(_good_row(Option_D="X"))
        assert valid is False


# ------------------------------------------------------------------
# determine_verdict
# ------------------------------------------------------------------

class TestDetermineVerdict:
    def test_all_pass(self):
        assert determine_verdict(CheckResult.PASS, CheckResult.PASS, CheckResult.PASS) == Verdict.PASS

    def test_not_answerable_wins(self):
        # Even if answer matches and explanation is fine, not-answerable dominates
        assert determine_verdict(CheckResult.FAIL, CheckResult.PASS, CheckResult.PASS) == Verdict.NOT_ANSWERABLE

    def test_wrong_answer_second(self):
        assert determine_verdict(CheckResult.PASS, CheckResult.FAIL, CheckResult.PASS) == Verdict.WRONG_ANSWER

    def test_bad_explanation_third(self):
        assert determine_verdict(CheckResult.PASS, CheckResult.PASS, CheckResult.FAIL) == Verdict.BAD_EXPLANATION

    def test_na_explanation_still_passes(self):
        # Missing explanation → N/A, but not a failure
        assert determine_verdict(CheckResult.PASS, CheckResult.PASS, CheckResult.NA) == Verdict.PASS


# ------------------------------------------------------------------
# map_check
# ------------------------------------------------------------------

class TestMapCheck:
    def test_pass(self):
        assert map_check("PASS") == CheckResult.PASS

    def test_fail(self):
        assert map_check("FAIL") == CheckResult.FAIL

    def test_na(self):
        assert map_check("N/A") == CheckResult.NA

    def test_empty(self):
        assert map_check("") == CheckResult.NA

    def test_unknown(self):
        assert map_check("MAYBE") == CheckResult.NA


# ------------------------------------------------------------------
# LLMJudge.parse_response
# ------------------------------------------------------------------

class TestParseResponse:
    def _judge(self) -> MockJudge:
        return MockJudge("{}")  # raw doesn't matter for this test class

    def test_bare_json(self):
        raw = '{"answerable":"PASS","llm_answer":"C","answer_match":"PASS","explanation_consistent":"PASS","confidence":0.95,"rationale":"Correct."}'
        result = self._judge().parse_response(raw)
        assert result is not None
        assert result["llm_answer"] == "C"
        assert result["confidence"] == 0.95

    def test_fenced_json(self):
        raw = '```json\n{"answerable":"FAIL","llm_answer":"B","answer_match":"N/A","explanation_consistent":"N/A","confidence":0.4,"rationale":"Options degenerate."}\n```'
        result = self._judge().parse_response(raw)
        assert result is not None
        assert result["answerable"] == "FAIL"

    def test_trailing_comma_fixed(self):
        raw = '{"answerable":"PASS","llm_answer":"A","answer_match":"PASS","explanation_consistent":"N/A","confidence":0.8,"rationale":"ok",}'
        result = self._judge().parse_response(raw)
        assert result is not None

    def test_no_json_returns_none(self):
        raw = "I cannot evaluate this question."
        result = self._judge().parse_response(raw)
        assert result is None


# ------------------------------------------------------------------
# Full judge_row integration with mock
# ------------------------------------------------------------------

class TestJudgeRow:
    def _run(self, row: dict, raw_response: str) -> RowResult:
        judge = MockJudge(raw_response)
        return asyncio.get_event_loop().run_until_complete(judge_row(row, judge))

    def test_correct_answer_produces_pass(self):
        raw = '{"answerable":"PASS","llm_answer":"C","answer_match":"PASS","explanation_consistent":"PASS","confidence":0.9,"rationale":"Softmax is standard."}'
        result = self._run(_good_row(), raw)
        assert result.verdict == Verdict.PASS
        assert result.llm_answer == "C"

    def test_wrong_stored_answer_detected(self):
        # Stored says C, LLM says A
        raw = '{"answerable":"PASS","llm_answer":"A","answer_match":"FAIL","explanation_consistent":"PASS","confidence":0.85,"rationale":"ReLU is correct here."}'
        result = self._run(_good_row(), raw)
        assert result.verdict == Verdict.WRONG_ANSWER
        assert result.stored_answer == "C"
        assert result.llm_answer == "A"

    def test_bad_explanation_detected(self):
        raw = '{"answerable":"PASS","llm_answer":"C","answer_match":"PASS","explanation_consistent":"FAIL","confidence":0.9,"rationale":"Explanation describes option A."}'
        result = self._run(_good_row(), raw)
        assert result.verdict == Verdict.BAD_EXPLANATION

    def test_invalid_input_row_skips_llm(self):
        row = _good_row(Option_A="")
        # Even if judge returns PASS, the pre-check should catch it
        raw = '{"answerable":"PASS","llm_answer":"C","answer_match":"PASS","explanation_consistent":"PASS","confidence":0.9,"rationale":"fine"}'
        result = self._run(row, raw)
        assert result.verdict == Verdict.INVALID_INPUT

    def test_judge_error_produces_error_verdict(self):
        judge = MockJudge("")  # empty response simulates failure
        result = asyncio.get_event_loop().run_until_complete(judge_row(_good_row(), judge))
        assert result.verdict == Verdict.ERROR

    def test_missing_explanation_is_na_not_fail(self):
        row = _good_row(Explanation="")
        raw = '{"answerable":"PASS","llm_answer":"C","answer_match":"PASS","explanation_consistent":"N/A","confidence":0.9,"rationale":"No explanation."}'
        result = self._run(row, raw)
        assert result.explanation_consistent == CheckResult.NA
        assert result.verdict == Verdict.PASS  # N/A does not fail


# ------------------------------------------------------------------
# accumulate / EvalReport counters
# ------------------------------------------------------------------

class TestAccumulate:
    def _report(self) -> EvalReport:
        return EvalReport(excel_path="test.xlsx", provider="ollama", model="qwen2.5:7b", total_rows=5)

    def _result(self, verdict: Verdict, stored="C", llm="C") -> RowResult:
        return RowResult(
            question_id="x",
            question_text="q",
            stored_answer=stored,
            llm_answer=llm,
            answerable=CheckResult.PASS,
            answer_match=CheckResult.PASS if verdict != Verdict.WRONG_ANSWER else CheckResult.FAIL,
            explanation_consistent=CheckResult.PASS,
            verdict=verdict,
            confidence=0.9,
            rationale="ok",
        )

    def test_pass_increments(self):
        report = self._report()
        accumulate(report, self._result(Verdict.PASS))
        assert report.passed == 1
        assert report.judged == 1

    def test_wrong_answer_increments_and_maps(self):
        report = self._report()
        accumulate(report, self._result(Verdict.WRONG_ANSWER, stored="C", llm="A"))
        assert report.wrong_answer == 1
        assert report.disagreement_map.get("C->A") == 1

    def test_pass_rate_calculation(self):
        report = self._report()
        accumulate(report, self._result(Verdict.PASS))
        accumulate(report, self._result(Verdict.WRONG_ANSWER, stored="B", llm="D"))
        accumulate(report, self._result(Verdict.INVALID_INPUT))
        # answerable_rows = 3 - 1 invalid - 0 errors = 2
        # passed = 1, so pass_rate = 0.5
        assert report.answerable_rows == 2
        assert abs(report.pass_rate - 0.5) < 1e-9
