"""
Markdown and Text file extractor for MCQ parsing.
Uses a cascading strategy: Regex Fast Path -> LLM Smart Fallback with Quality Validation.
"""

import json
import random
import asyncio
from typing import List, Union
from pathlib import Path
import re

from extractors.base_extractor import BaseExtractor
from config.schemas import MCQ
from utils.text_processor import extract_option_text
from validators.quality_validator import QualityValidator
from classifiers.prompt_templates import get_universal_extraction_prompt


class MarkdownTxtExtractor(BaseExtractor):
    """Extract MCQs from local Markdown (.md) or Text (.txt) files."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = QualityValidator()

    async def extract(self, source: Union[str, Path]) -> List[MCQ]:
        """
        Extract MCQs from markdown or text files with quality validation.

        Flow:
        1. Read text from file
        2. Try regex for structured MCQs (fast path)
        3. If not found or quality < 80%, use LLM extraction (smart path)
        4. Validate all MCQs through quality filter
        5. Return validated MCQs
        """
        source_path = Path(source)
        if not source_path.exists():
            self.log(f"File not found: {source_path}", 'error')
            return []

        self.log(f"Extracting from text/markdown file: {source_path.name}")

        try:
            full_text = source_path.read_text(encoding='utf-8', errors='ignore')

            if not full_text or len(full_text.strip()) < 50:
                self.log(f"No meaningful text extracted from {source_path.name}", 'warning')
                return []

            # 1. Try regex extraction for A) B) C) D) formatted MCQs
            regex_mcqs = self._parse_mcq_text(full_text, str(source))

            if regex_mcqs:
                # Validate regex-extracted MCQs
                passed, failed, stats = self.validator.batch_validate(regex_mcqs)
                self.log(f"Regex extraction: {len(passed)}/{len(regex_mcqs)} passed quality check "
                         f"({stats['pass_rate']*100:.1f}%)")

                # If pass rate is good (>80%), return them
                if stats['pass_rate'] >= 0.8:
                    return passed

                self.log("Regex quality insufficient, falling back to LLM extraction for upgrade...")

            # 2. LLM smart path fallback
            if self.llm_client:
                self.log("Using LLM for extraction with quality validation...")
                mcqs = await self._llm_extract(full_text, str(source))
                self.log(f"Extracted {len(mcqs)} quality-validated MCQs from {source_path.name}")
                return mcqs
            else:
                self.log("No LLM client available for smart extraction", 'warning')
                return []

        except Exception as e:
            self.log(f"Error extracting from file {source}: {e}", 'error')
            return []

    async def _llm_extract(self, text: str, source: str) -> List[MCQ]:
        """LLM-based extraction with category distribution and quality validation."""
        batches = self._split_for_llm(text)
        self.log(f"Split text into {len(batches)} batches for LLM processing")

        all_mcqs = []

        for i, batch in enumerate(batches, 1):
            self.log(f"Processing batch {i}/{len(batches)} ({len(batch)} chars)...")

            # Extract with distribution (50/25/25)
            batch_mcqs = await self._extract_batch_with_distribution(batch, source)

            # Validate quality
            if batch_mcqs:
                passed, failed, stats = self.validator.batch_validate(batch_mcqs)

                self.log(f"Batch {i}: {stats['pass_rate']*100:.1f}% pass rate "
                         f"({len(passed)}/{len(batch_mcqs)} passed)")

                # Log first failure for debugging
                if failed:
                    mcq, reason = failed[0]
                    self.log(f"Quality fail example: {mcq.question_text[:50]}... | Reason: {reason}", 'warning')

                all_mcqs.extend(passed)

        return all_mcqs

    def _has_existing_mcqs(self, text: str) -> bool:
        """Detect whether text contains structured questions with A/B/C/D options."""
        option_markers = sum(1 for m in ['A)', 'B)', 'C)', 'D)', '(a)', '(b)', '(c)', '(d)'] if m in text)
        tabular_answers = len(re.findall(r'\t[A-D]\s*$', text, re.MULTILINE))
        return option_markers >= 4 or tabular_answers >= 2

    def _has_embedded_answers(self, text: str) -> bool:
        """Detect whether the text already contains an inline answer key."""
        answer_markers = len(re.findall(r'\b[Aa]nswer\s*[:\-]?\s*[A-Da-d]\b', text))
        tabular_answers = len(re.findall(r'\t[A-D]\s*$', text, re.MULTILINE))
        detailed_answers = len(re.findall(r'^\d+\.\s*\([a-dA-D]\)', text, re.MULTILINE))
        return answer_markers >= 2 or tabular_answers >= 2 or detailed_answers >= 3

    async def _extract_batch_with_distribution(self, text: str, source: str) -> List[MCQ]:
        """Extract MCQs from a text batch using one of three strategies."""
        has_questions = self._has_existing_mcqs(text)
        has_answers = self._has_embedded_answers(text)

        if has_questions and has_answers:
            self.log("Questions + answers detected — preserving existing answers")
            prompt = get_universal_extraction_prompt(text)
            response = await self._call_llm_with_retry(prompt)
            if not response:
                return []
            mcqs_data = self._parse_llm_response(response)
            return [mcq for data in mcqs_data
                    if (mcq := self._create_mcq_with_shuffle(data, source))]

        if has_questions and not has_answers:
            self.log("Questions without answers detected — LLM will reason correct answers")
            prompt = self._get_answer_verification_prompt(text)
            response = await self._call_llm_with_retry(prompt)
            if not response:
                return []
            mcqs_data = self._parse_llm_response(response)
            return [mcq for data in mcqs_data
                    if (mcq := self._create_mcq_with_shuffle(data, source))]

        # Prose content — generate new MCQs with 50/25/25 distribution
        estimated_questions = max(2, len(text) // 400)
        num_conceptual = int(estimated_questions * 0.5)
        num_mathematical = int(estimated_questions * 0.25)
        num_application = estimated_questions - num_conceptual - num_mathematical

        all_mcqs = []
        for category, target_count in [
            ('Conceptual', num_conceptual),
            ('Mathematical', num_mathematical),
            ('Application', num_application)
        ]:
            if target_count == 0:
                continue

            prompt = self._get_lightweight_prompt(category, text, target_count)
            response = await self._call_llm_with_retry(prompt)
            if not response:
                continue

            mcqs_data = self._parse_llm_response(response)
            mcqs_data = mcqs_data[:target_count]
            for data in mcqs_data:
                data['category'] = category
                mcq = self._create_mcq_with_shuffle(data, source)
                if mcq:
                    all_mcqs.append(mcq)

        return all_mcqs

    def _get_answer_verification_prompt(self, content: str) -> str:
        """Prompt for content that already has questions + options but NO embedded answer key."""
        return f"""You are an expert AI/ML educator. The following content contains multiple-choice questions with options but NO answer key.

Your job for EACH question:
1. Copy the question text and all four options EXACTLY as written — do not rephrase
2. Use your knowledge to determine which option is CORRECT
3. Write a concise explanation (2-3 sentences) justifying why that answer is correct and why the others are wrong
4. Assign: category (Conceptual/Mathematical/Application), topic (AI/ML/Data Science/System Design), difficulty (Easy/Medium/Hard)

CONTENT:
{content}

Rules:
- NEVER guess randomly — reason through each question carefully using your knowledge
- The correct_answer must be the letter (A/B/C/D) of the genuinely correct option
- If a question has option (a)/(b)/(c)/(d) format, map them to A/B/C/D in order
- Do not skip any question
- Return ONLY a valid JSON array, no markdown fencing

[
  {{
    "question_text": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "B",
    "explanation": "Option B is correct because... Options A, C, and D are wrong because...",
    "category": "Conceptual",
    "topic": "ML",
    "difficulty": "Medium"
  }}
]"""

    def _get_lightweight_prompt(self, category: str, content: str, target_count: int) -> str:
        """Generation prompt for prose content with no existing questions."""
        category_desc = {
            'Conceptual': 'focuses on understanding concepts, definitions, and theories',
            'Mathematical': 'requires calculations, formulas, or numerical reasoning',
            'Application': 'tests practical application, scenarios, or problem-solving'
        }

        return f"""Generate {target_count} multiple choice questions (MCQs) that {category_desc.get(category, category)} based on the following content.

Requirements:
- Each question must be detailed (at least 20 words), testing reasoning not just recall
- Each option must be plausible and similar in length
- Include a detailed explanation (at least 30 words)
- Set difficulty to "Medium" or "Hard"
- Set topic to one of: "AI", "ML", "Data Science", "System Design"

CONTENT:
{content}

Generate ONLY a JSON array with no markdown:

[
  {{"question_text": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "A", "explanation": "...", "difficulty": "Medium", "topic": "Data Science"}}
]

Return ONLY valid JSON array, no additional text."""

    async def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Call LLM with exponential backoff retry for rate limits."""
        for attempt in range(max_retries):
            try:
                # Check if using Gemini or OpenAI-compatible API
                if hasattr(self.llm_client, 'client') and hasattr(self.llm_client.client, 'models'):
                    # Gemini API
                    response = self.llm_client.client.models.generate_content(
                        model=self.llm_client.model_name,
                        contents=prompt
                    )
                    return response.text
                else:
                    # OpenAI-compatible API (Groq, OpenAI, Together)
                    response = await self.llm_client.chat.completions.create(
                        model=self.llm_client.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7
                    )
                    return response.choices[0].message.content

            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'rate_limit' in error_str.lower():
                    wait_time = min(60 * (attempt + 1), 120)
                    self.log(f"Rate limited, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                    await asyncio.sleep(wait_time)
                else:
                    self.log(f"LLM call error: {e}", 'error')
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                    else:
                        return None

        self.log(f"Failed after {max_retries} retries", 'error')
        return None

    def _create_mcq_with_shuffle(self, data: dict, source: str) -> MCQ:
        """Create MCQ from LLM response data with answer randomization."""
        try:
            import uuid
            from datetime import datetime

            options = [data['option_a'], data['option_b'], data['option_c'], data['option_d']]
            correct_letter = data['correct_answer'].strip().upper()

            if correct_letter not in ['A', 'B', 'C', 'D']:
                self.log(f"Invalid correct_answer '{correct_letter}', skipping", 'warning')
                return None

            correct_idx = ord(correct_letter) - ord('A')

            # Shuffle by index
            indices = list(range(4))
            random.shuffle(indices)
            options = [options[i] for i in indices]
            new_correct_idx = indices.index(correct_idx)
            new_correct_letter = chr(ord('A') + new_correct_idx)

            # Validate category
            category = data.get('category', 'Conceptual')
            if category not in ['Mathematical', 'Application', 'Conceptual']:
                category = 'Conceptual'

            # Validate topic
            topic = data.get('topic', 'Data Science')
            valid_topics = ['AI', 'ML', 'Data Science', 'System Design']
            if topic not in valid_topics:
                topic = 'Data Science'

            # Validate difficulty
            difficulty = data.get('difficulty', 'Medium')
            if difficulty not in ['Easy', 'Medium', 'Hard']:
                difficulty = 'Medium'

            mcq = MCQ(
                question_id=str(uuid.uuid4()),
                question_text=data['question_text'].strip(),
                option_a=options[0],
                option_b=options[1],
                option_c=options[2],
                option_d=options[3],
                correct_answer=new_correct_letter,
                explanation=data.get('explanation', ''),
                category=category,
                topic=topic,
                difficulty=difficulty,
                source=source,
                date_added=datetime.now()
            )

            return mcq

        except Exception as e:
            self.log(f"Error creating MCQ: {e}", 'warning')
            return None

    def _split_for_llm(self, text: str, max_chars: int = 4000) -> List[str]:
        """Split text into LLM-friendly batches without breaking content."""
        if len(text) <= max_chars:
            return [text]

        paragraphs = text.split('\n\n')
        if len(paragraphs) < 3:
            paragraphs = text.split('\n')

        batches = []
        current_batch = []
        current_length = 0

        for para in paragraphs:
            if current_length + len(para) > max_chars and current_batch:
                batches.append('\n'.join(current_batch))
                current_batch = [para]
                current_length = len(para)
            else:
                current_batch.append(para)
                current_length += len(para)

        if current_batch:
            batches.append('\n'.join(current_batch))

        return batches

    def _parse_llm_response(self, response_text: str) -> List[dict]:
        """Parse LLM JSON response with cleanup."""
        required = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']

        try:
            text = response_text.strip()

            # Strip markdown code fences
            if text.startswith('```json'):
                text = text.split('\n', 1)[1] if '\n' in text else text[7:]
            elif text.startswith('```'):
                text = text.split('\n', 1)[1] if '\n' in text else text[3:]
            if text.endswith('```'):
                text = text.rsplit('```', 1)[0]
            text = text.strip()

            # Find JSON array boundaries
            start = text.find('[')
            end = text.rfind(']')
            if start != -1 and end != -1:
                text = text[start:end + 1]

            # Try direct parse first
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                # Fix common JSON issues
                text = re.sub(r'\}\s*\{', '},{', text)
                text = re.sub(r',\s*\]', ']', text)
                text = re.sub(r',\s*\}', '}', text)
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    data = self._extract_json_objects(text)

            if not isinstance(data, list):
                data = [data] if isinstance(data, dict) else []

            valid = [item for item in data if isinstance(item, dict) and all(f in item for f in required)]
            return valid

        except Exception as e:
            self.log(f"Error parsing LLM response: {e}", 'error')
            return []

    def _extract_json_objects(self, text: str) -> List[dict]:
        """Extract individual JSON objects from malformed response."""
        objects = []
        depth = 0
        start = None

        for i, char in enumerate(text):
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    try:
                        obj = json.loads(text[start:i + 1])
                        objects.append(obj)
                    except json.JSONDecodeError:
                        pass
                    start = None

        return objects

    def _parse_mcq_text(self, text: str, source: str) -> List[MCQ]:
        """Parse MCQs from extracted text using regex (fast fallback)."""
        mcqs = []

        mcq_markers = ['A)', 'B)', 'C)', 'D)', '(a)', '(b)', '(c)', '(d)']
        marker_count = sum(1 for marker in mcq_markers if marker in text)
        if marker_count < 3:
            return []

        pattern_numbered = r'(?P<num>\d+)\.\s*(?P<question>.+?\?)\s*\(a\)\s*(?P<opt_a>.+?)\s*\(b\)\s*(?P<opt_b>.+?)\s*\(c\)\s*(?P<opt_c>.+?)\s*\(d\)\s*(?P<opt_d>.+?)(?=\d+\.|$)'

        for match in re.finditer(pattern_numbered, text, re.DOTALL | re.IGNORECASE):
            mcq = self._create_mcq(
                question_text=match.group('question').strip(),
                option_a=extract_option_text(match.group('opt_a').strip()),
                option_b=extract_option_text(match.group('opt_b').strip()),
                option_c=extract_option_text(match.group('opt_c').strip()),
                option_d=extract_option_text(match.group('opt_d').strip()),
                source=source
            )
            if mcq:
                mcqs.append(mcq)

        if not mcqs:
            pattern2 = r'(?P<question>.+?\?)\s*(?:A\)|a\))\s*(?P<opt_a>.+?)\s*(?:B\)|b\))\s*(?P<opt_b>.+?)\s*(?:C\)|c\))\s*(?P<opt_c>.+?)\s*(?:D\)|d\))\s*(?P<opt_d>.+?)(?:\n|$)'

            for match in re.finditer(pattern2, text, re.DOTALL | re.MULTILINE):
                mcq = self._create_mcq(
                    question_text=match.group('question').strip(),
                    option_a=extract_option_text(match.group('opt_a').strip()),
                    option_b=extract_option_text(match.group('opt_b').strip()),
                    option_c=extract_option_text(match.group('opt_c').strip()),
                    option_d=extract_option_text(match.group('opt_d').strip()),
                    source=source
                )
                if mcq:
                    mcqs.append(mcq)

        if mcqs:
            self._extract_answers(text, mcqs)

        return mcqs

    def _extract_answers(self, text: str, mcqs: List[MCQ]):
        """Extract answers from answer key section if present."""
        answer_section_pattern = r'(?:Answer\s+Key|Answers|Solutions)[\s:]*(.+?)(?:\n\n|\Z)'
        match = re.search(answer_section_pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            answer_text = match.group(1)
            answer_matches = re.findall(r'([A-Da-d])', answer_text)

            for i, answer in enumerate(answer_matches):
                if i < len(mcqs):
                    mcqs[i].correct_answer = answer.upper()
