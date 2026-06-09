"""
QuestionsOnlyPDFExtractor: reads a PDF that contains bare questions (no options),
generates 4 options + correct answer + explanation + category/topic/difficulty
for each question via LLM, and returns standard MCQ objects.

Bare-question detection:
  A line is treated as a question if it ends with '?' and is NOT immediately
  followed by option markers (A), B), A., B., etc.).  Lines that are part of
  already-formed MCQs (options present) are skipped entirely.

LLM generation:
  One LLM call per question asking for a JSON object with:
    option_a, option_b, option_c, option_d,
    correct_answer (A/B/C/D),
    explanation,
    category (Conceptual|Mathematical|Application),
    topic (AI|ML|Data Science|System Design),
    difficulty (Easy|Medium|Hard)
"""

import asyncio
import json
import logging
import re
import random
from pathlib import Path
from typing import List, Optional, Union

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from extractors.base_extractor import BaseExtractor
from config.schemas import MCQ

logger = logging.getLogger(__name__)

# Option line: A) / B) / C) / D) at the start of a line (with any spacing)
_OPTION_LINE = re.compile(r"^\s*[A-D]\s*[).]\s+\S", re.IGNORECASE)

# "Question N:" or "Question N." header that introduces a formed MCQ block
_MCQ_HEADER = re.compile(r"^\s*Question\s+\d+\s*[:.)]", re.IGNORECASE)

# A question sentence: must end with ?
_QUESTION_END = re.compile(r"\?\s*$")

# Noise lines to discard (nav/metadata from scraped PDFs)
_NOISE = re.compile(
    r"(Tags:|There are \d+ questions|Take a part|View All Discussion"
    r"|Last Updated|DiscussComments?|^\s*Question\s+\d+\s*$"
    r"|Write down your answers|speak them out loud|record yourself"
    r"|covers data.structures essentials|interview prep\b)",
    re.IGNORECASE,
)

# Page/section titles that are not questions
_TITLE = re.compile(
    r"^(Comprehensive|Top \d+|Chapter|Section|Part|Write down)\b",
    re.IGNORECASE,
)

# Orphan continuation fragments: short lines that are clearly the tail of a
# previous option that wrapped onto a new line (e.g. "to the training data")
_ORPHAN_FRAGMENT = re.compile(
    r"^(to the |of the |in the |for the |at the |by the |from the |a model |the model )",
    re.IGNORECASE,
)


def _is_option_line(line: str) -> bool:
    return bool(_OPTION_LINE.match(line))


def _is_mcq_header(line: str) -> bool:
    """True for 'Question 1:' / 'Question 2.' style headers."""
    return bool(_MCQ_HEADER.match(line))


def _is_noise(line: str) -> bool:
    return bool(_NOISE.search(line)) or bool(_TITLE.match(line))


def _skip_mcq_block(lines: List[str], start: int) -> int:
    """
    Given that lines[start] is an MCQ header or a question followed by options,
    advance the index past the entire block (question + all 4 option lines).
    Returns the index of the first line after the block.
    """
    i = start + 1
    # Skip the question text lines (until we hit an option or blank)
    while i < len(lines):
        l = lines[i].strip()
        if not l or _is_option_line(l) or _is_mcq_header(l):
            break
        i += 1
    # Skip option lines A) B) C) D)
    option_count = 0
    while i < len(lines) and option_count < 4:
        l = lines[i].strip()
        if _is_option_line(l):
            option_count += 1
            i += 1
        elif not l:
            i += 1  # blank lines between options are ok
        else:
            break
    return i


def _extract_bare_questions(full_text: str) -> List[str]:
    """
    Parse raw PDF text and return only bare question strings.

    Strategy:
    1. Split into lines.
    2. When a 'Question N:' header is seen, skip the entire MCQ block.
    3. When a line is an option (A) B) C) D)), skip it.
    4. Accumulate remaining lines into question candidates (end at '?').
    5. After accumulation, if the very next content line is an option → skip
       (bare question immediately followed by options = formed MCQ).
    6. Deduplicate.
    """
    text = full_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    questions: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip blank, noise, titles, orphan continuation fragments
        if not line or _is_noise(line) or _ORPHAN_FRAGMENT.match(line):
            i += 1
            continue

        # Skip option lines (stray A)/B)/C)/D) not already consumed)
        if _is_option_line(line):
            i += 1
            continue

        # Skip formed MCQ blocks introduced by "Question N:" header
        if _is_mcq_header(line):
            i = _skip_mcq_block(lines, i)
            continue

        # --- Accumulate a bare question candidate ---
        # A candidate starts here and continues until:
        #   - we've seen a '?' (end of question)
        #   - or we hit a blank / option / MCQ header

        # Strip any leading non-question prefix on this line
        # (e.g. page title runs into first question on same line)
        clean_line = line
        if '?' not in line:
            # If the line has no ?, treat it as a prefix only if it looks like
            # a title — skip it entirely and start fresh on next line
            if not re.search(r'\b(what|which|how|why|when|where|who|is|are|does|do|can|would|should|explain|describe)\b', line, re.IGNORECASE):
                i += 1
                continue

        candidate_parts = [clean_line]
        j = i + 1
        while j < len(lines):
            nxt = lines[j].strip()
            if not nxt:
                break
            if _is_option_line(nxt) or _is_mcq_header(nxt) or _is_noise(nxt):
                break
            # Stop accumulating once we've completed a question sentence
            if _QUESTION_END.search(" ".join(candidate_parts)):
                break
            candidate_parts.append(nxt)
            j += 1

        candidate = re.sub(r"\s+", " ", " ".join(candidate_parts)).strip()

        # Must end with ?
        if not _QUESTION_END.search(candidate):
            i = j
            continue

        # Skip if immediately followed by an option line (= formed MCQ without header)
        k = j
        while k < len(lines) and not lines[k].strip():
            k += 1
        if k < len(lines) and _is_option_line(lines[k].strip()):
            i = _skip_mcq_block(lines, i)
            continue

        if len(candidate) > 20:
            questions.append(candidate)

        i = j

    # Deduplicate preserving order
    seen: set = set()
    unique: List[str] = []
    for q in questions:
        key = re.sub(r"\s+", " ", q).lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(q)

    return unique


# ------------------------------------------------------------------
# LLM generation prompt
# ------------------------------------------------------------------

def _make_generation_prompt(question: str) -> str:
    return f"""You are an expert ML/AI educator creating MAANG-level interview MCQs.

Given this question, generate 4 answer options, identify the correct one, write a
clear explanation, and classify the question.

Question:
{question}

Rules:
- All 4 options must be plausible; only ONE must be correct.
- Distractors should reflect common misconceptions, not obvious nonsense.
- Explanation must justify WHY the correct answer is right AND briefly why the
  others are wrong (2-4 sentences).
- category: one of Conceptual | Mathematical | Application
- topic: one of AI | ML | Data Science | System Design
- difficulty: one of Easy | Medium | Hard

Respond with ONLY a valid JSON object, no markdown fences:
{{
  "option_a": "...",
  "option_b": "...",
  "option_c": "...",
  "option_d": "...",
  "correct_answer": "A",
  "explanation": "...",
  "category": "Conceptual",
  "topic": "ML",
  "difficulty": "Medium"
}}"""


# ------------------------------------------------------------------
# Extractor
# ------------------------------------------------------------------

class QuestionsOnlyPDFExtractor(BaseExtractor):
    """
    Extract bare questions from a PDF and use an LLM to generate full MCQs.

    One LLM call per question: generates options, correct answer, explanation,
    and classification (category/topic/difficulty) in a single shot.
    """

    def __init__(self, *args, concurrency: int = 2, **kwargs):
        super().__init__(*args, **kwargs)
        self._sem = asyncio.Semaphore(concurrency)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def extract(self, source: Union[str, Path]) -> List[MCQ]:
        if pdfplumber is None:
            self.log("pdfplumber not installed. Run: pip install pdfplumber", "error")
            return []

        pdf_path = Path(source)
        if not pdf_path.exists():
            self.log(f"PDF not found: {pdf_path}", "error")
            return []

        self.log(f"Reading PDF: {pdf_path.name}")
        full_text = self._read_pdf(pdf_path)
        if not full_text or len(full_text.strip()) < 30:
            self.log("No text extracted from PDF", "warning")
            return []

        bare_questions = _extract_bare_questions(full_text)
        self.log(f"Found {len(bare_questions)} bare questions to generate MCQs for")

        if not bare_questions:
            self.log("No bare questions found — the PDF may already contain fully-formed MCQs.", "warning")
            return []

        tasks = [
            asyncio.create_task(self._generate_mcq(q, str(pdf_path)))
            for q in bare_questions
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        mcqs: List[MCQ] = []
        for q, res in zip(bare_questions, results):
            if isinstance(res, Exception):
                self.log(f"Generation failed for: {q[:60]}... — {res}", "warning")
            elif res is not None:
                mcqs.append(res)

        self.log(f"Generated {len(mcqs)}/{len(bare_questions)} MCQs successfully")
        return mcqs

    # ------------------------------------------------------------------
    # PDF text extraction
    # ------------------------------------------------------------------

    def _read_pdf(self, path: Path) -> str:
        try:
            pages = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
            return "\n".join(pages)
        except Exception as exc:
            self.log(f"pdfplumber failed: {exc}", "error")
            return ""

    # ------------------------------------------------------------------
    # LLM generation
    # ------------------------------------------------------------------

    async def _generate_mcq(self, question: str, source: str) -> Optional[MCQ]:
        prompt = _make_generation_prompt(question)
        async with self._sem:
            raw = await self._call_llm(prompt)
        if not raw:
            return None
        return self._parse_response(raw, question, source)

    async def _call_llm(self, prompt: str) -> Optional[str]:
        if self.llm_client is None:
            self.log("No LLM client configured", "error")
            return None

        for attempt in range(3):
            try:
                # Gemini path
                if hasattr(self.llm_client, "client") and hasattr(
                    self.llm_client.client, "models"
                ):
                    response = self.llm_client.client.models.generate_content(
                        model=self.llm_client.model,
                        contents=prompt,
                    )
                    return response.text

                # OpenAI-compatible path (Ollama, Groq, OpenAI, DeepSeek …)
                model_name = (
                    getattr(self.llm_client, "model_name", None)
                    or getattr(self.llm_client, "model", None)
                    or "qwen2.5:7b"
                )
                response = await self.llm_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                return response.choices[0].message.content

            except Exception as exc:
                msg = str(exc)
                if "429" in msg or "rate" in msg.lower():
                    wait = min(60 * (attempt + 1), 120)
                    self.log(f"Rate limit, waiting {wait}s (attempt {attempt+1}/3)", "warning")
                    await asyncio.sleep(wait)
                else:
                    self.log(f"LLM call failed: {exc}", "error")
                    return None

        return None

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(self, raw: str, question: str, source: str) -> Optional[MCQ]:
        text = raw.strip()

        # Strip markdown fences
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text.rstrip()).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            self.log(f"No JSON in response for: {question[:50]}", "warning")
            return None
        text = text[start : end + 1]

        # Fix trailing commas
        text = re.sub(r",\s*\}", "}", text)
        text = re.sub(r",\s*\]", "]", text)

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            self.log(f"JSON parse error ({exc}): {text[:200]}", "warning")
            return None

        option_a = str(data.get("option_a", "")).strip()
        option_b = str(data.get("option_b", "")).strip()
        option_c = str(data.get("option_c", "")).strip()
        option_d = str(data.get("option_d", "")).strip()
        correct_raw = str(data.get("correct_answer", "")).strip().upper()
        explanation = str(data.get("explanation", "")).strip()

        # Validate
        if not all([option_a, option_b, option_c, option_d]):
            self.log(f"Missing options in response for: {question[:50]}", "warning")
            return None
        if correct_raw not in ("A", "B", "C", "D"):
            self.log(f"Invalid correct_answer '{correct_raw}', defaulting to A", "warning")
            correct_raw = "A"
        if not explanation or len(explanation) < 20:
            self.log(f"Explanation too short for: {question[:50]}", "warning")
            return None

        # Shuffle options (prevent position bias)
        options = [option_a, option_b, option_c, option_d]
        correct_idx = ord(correct_raw) - ord("A")
        indices = [0, 1, 2, 3]
        random.shuffle(indices)
        shuffled = [options[i] for i in indices]
        new_correct_idx = indices.index(correct_idx)
        new_correct = chr(ord("A") + new_correct_idx)

        # Map category/topic/difficulty — accept LLM value or default
        raw_category = str(data.get("category", "")).strip()
        category = raw_category if raw_category in ("Conceptual", "Mathematical", "Application") else "Conceptual"

        raw_topic = str(data.get("topic", "")).strip()
        topic = raw_topic if raw_topic in ("AI", "ML", "Data Science", "System Design") else "ML"

        raw_diff = str(data.get("difficulty", "")).strip()
        difficulty = raw_diff if raw_diff in ("Easy", "Medium", "Hard") else "Medium"

        return self._create_mcq_full(
            question_text=question,
            option_a=shuffled[0],
            option_b=shuffled[1],
            option_c=shuffled[2],
            option_d=shuffled[3],
            source=source,
            correct_answer=new_correct,
            explanation=explanation,
            category=category,
            topic=topic,
            difficulty=difficulty,
        )

    def _create_mcq_full(
        self,
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        source: str,
        correct_answer: str,
        explanation: str,
        category: str,
        topic: str,
        difficulty: str,
    ) -> Optional[MCQ]:
        from utils.text_processor import clean_text

        mcq = MCQ(
            question_text=clean_text(question_text),
            option_a=clean_text(option_a),
            option_b=clean_text(option_b),
            option_c=clean_text(option_c),
            option_d=clean_text(option_d),
            source=source,
            correct_answer=correct_answer,
            explanation=clean_text(explanation),
            category=category,
            topic=topic,
            difficulty=difficulty,
        )
        return mcq if mcq.is_valid() else None
