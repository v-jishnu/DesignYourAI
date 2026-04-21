"""
Content shape detector.

Given a blob of text, decides whether it looks like:
  - "mcq"   already-structured MCQs (question + A/B/C/D + answer marker)
  - "qa"    plain Q&A pairs (question text followed by answer text)
  - "prose" neither, just an article/page content

Pure heuristics, no LLM. Used by the drop-in ingestion CLI to preview
and by the GitHub markdown extractor to decide between direct Q&A parse
and prose-generation fallback.
"""

from dataclasses import dataclass
from typing import Literal
import re


Shape = Literal["mcq", "qa", "prose"]


@dataclass
class ShapeReport:
    shape: Shape
    mcq_markers: int
    qa_markers: int
    word_count: int
    note: str


_OPTION_PATTERN = re.compile(r"(?:^|\n)\s*[A-D][\)\.\:]\s+\S", re.MULTILINE)
_ANSWER_PATTERN = re.compile(r"(?i)(?:correct\s+answer|answer\s*[:\-])\s*[A-D]\b")
_Q_PREFIX_PATTERN = re.compile(r"(?im)^\s*Q\s*\d+\s*[:.\)]\s*\S")
_NUMBERED_Q_PATTERN = re.compile(r"(?m)^\s*\d{1,3}\.\s+.+\?")
_HEADING_Q_PATTERN = re.compile(r"(?m)^\s{0,3}#{2,4}\s+.+\?")


def detect_shape(text: str) -> ShapeReport:
    """Classify content shape."""
    if not text or not text.strip():
        return ShapeReport("prose", 0, 0, 0, "empty input")

    words = text.split()
    word_count = len(words)

    option_hits = len(_OPTION_PATTERN.findall(text))
    answer_hits = len(_ANSWER_PATTERN.findall(text))

    q_prefix_hits = len(_Q_PREFIX_PATTERN.findall(text))
    numbered_q_hits = len(_NUMBERED_Q_PATTERN.findall(text))
    heading_q_hits = len(_HEADING_Q_PATTERN.findall(text))
    qa_hits = q_prefix_hits + numbered_q_hits + heading_q_hits

    # MCQ shape: need at least ~4 option markers AND either an answer marker
    # or a high density of options (a real MCQ page has many A/B/C/D groups).
    if option_hits >= 4 and (answer_hits >= 1 or option_hits >= 8):
        return ShapeReport(
            "mcq",
            option_hits,
            qa_hits,
            word_count,
            f"{option_hits} option markers, {answer_hits} answer markers",
        )

    # Q&A shape: at least 3 distinct question markers
    if qa_hits >= 3:
        return ShapeReport(
            "qa",
            option_hits,
            qa_hits,
            word_count,
            f"{qa_hits} question markers "
            f"(Q#={q_prefix_hits}, numbered={numbered_q_hits}, heading={heading_q_hits})",
        )

    return ShapeReport(
        "prose",
        option_hits,
        qa_hits,
        word_count,
        f"no strong MCQ/QA markers (options={option_hits}, qa={qa_hits})",
    )
