"""
Verdict data structures for the evaluation pipeline.

These are intentionally separate from config.schemas.MCQ: an MCQ is the thing
being judged; these models hold the judgement. Keeping them apart means the
evaluator never has to mutate an MCQ to record a result.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List
from enum import Enum


class Verdict(str, Enum):
    """Overall verdict for a single MCQ row."""

    PASS = "PASS"                    # answerable, stored answer == LLM pick, explanation consistent
    WRONG_ANSWER = "WRONG_ANSWER"    # answerable, but stored answer disagrees with LLM pick
    BAD_EXPLANATION = "BAD_EXPLANATION"  # answer agrees, but explanation justifies a different option
    NOT_ANSWERABLE = "NOT_ANSWERABLE"    # options insufficient / ambiguous / degenerate
    INVALID_INPUT = "INVALID_INPUT"      # row is missing required fields (not the LLM's fault)
    ERROR = "ERROR"                  # judging failed (LLM/parse error) — re-run candidate


class CheckResult(str, Enum):
    """Tri-state result for an individual check."""

    PASS = "PASS"
    FAIL = "FAIL"
    NA = "N/A"  # check could not be applied (e.g. no explanation present to judge)


@dataclass
class RowResult:
    """The full evaluation result for one MCQ."""

    question_id: str
    question_text: str
    stored_answer: Optional[str]          # the Correct_Answer marked in the KB
    llm_answer: Optional[str]             # what the LLM independently picked, blind

    answerable: CheckResult               # check 1
    answer_match: CheckResult             # check 3 (stored == llm)
    explanation_consistent: CheckResult   # check 4

    verdict: Verdict
    confidence: float                     # 0.0–1.0 self-reported by the judge
    rationale: str                        # one-line LLM justification

    def to_row(self) -> Dict:
        """Flatten into the columns appended to the annotated Excel."""
        return {
            "Eval_Answerable": self.answerable.value,
            "Eval_LLM_Answer": self.llm_answer or "",
            "Eval_Answer_Match": self.answer_match.value,
            "Eval_Explanation_Consistent": self.explanation_consistent.value,
            "Eval_Verdict": self.verdict.value,
            "Eval_Confidence": round(self.confidence, 2),
            "Eval_Rationale": self.rationale,
        }

    def to_dict(self) -> Dict:
        d = asdict(self)
        # Enums -> their string values for clean JSON
        d["answerable"] = self.answerable.value
        d["answer_match"] = self.answer_match.value
        d["explanation_consistent"] = self.explanation_consistent.value
        d["verdict"] = self.verdict.value
        return d


@dataclass
class EvalReport:
    """Aggregate report across all judged rows."""

    excel_path: str
    provider: str
    model: str
    total_rows: int = 0
    judged: int = 0

    # Verdict tallies
    passed: int = 0
    wrong_answer: int = 0
    bad_explanation: int = 0
    not_answerable: int = 0
    invalid_input: int = 0
    errors: int = 0

    # Data-quality observations (not failures, but worth surfacing)
    missing_explanation: int = 0

    # Letters the LLM picked when it disagreed with the stored answer,
    # e.g. {"A->C": 4} means stored A, LLM said C.
    disagreement_map: Dict[str, int] = field(default_factory=dict)

    results: List[RowResult] = field(default_factory=list)

    @property
    def answerable_rows(self) -> int:
        """Rows the LLM could actually judge (excludes invalid/error)."""
        return self.judged - self.invalid_input - self.errors

    @property
    def wrong_answer_rate(self) -> float:
        """Wrong answers as a fraction of genuinely answerable rows.

        This is the headline number; it deliberately excludes invalid/incomplete
        rows so the metric reflects answer quality, not data completeness.
        """
        base = self.answerable_rows
        return self.wrong_answer / base if base else 0.0

    @property
    def pass_rate(self) -> float:
        base = self.answerable_rows
        return self.passed / base if base else 0.0

    def to_dict(self) -> Dict:
        d = {k: v for k, v in asdict(self).items() if k != "results"}
        d["wrong_answer_rate"] = round(self.wrong_answer_rate, 4)
        d["pass_rate"] = round(self.pass_rate, 4)
        d["answerable_rows"] = self.answerable_rows
        d["results"] = [r.to_dict() for r in self.results]
        return d
