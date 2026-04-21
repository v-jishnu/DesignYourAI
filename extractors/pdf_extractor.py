"""
PDF extractor for MCQ extraction from PDF documents.
LLM-first approach with MAANG-level quality validation.
"""

import json
import random
import asyncio
from typing import List, Union
from pathlib import Path
import re
import tempfile
import aiohttp

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from extractors.base_extractor import BaseExtractor
from config.schemas import MCQ
from utils.text_processor import extract_option_text
from validators.quality_validator import QualityValidator


class PDFExtractor(BaseExtractor):
    """Extract MCQs from PDF documents with MAANG-level quality validation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = QualityValidator()

    async def extract(self, source: Union[str, Path]) -> List[MCQ]:
        """
        Extract MCQs from PDF with quality validation and distribution enforcement.

        Flow:
        1. Extract text
        2. Try regex for structured MCQs (fast path)
        3. If not found or quality < 80%, use LLM extraction (smart path)
        4. Validate all MCQs through quality filter
        5. Return validated MCQs

        Args:
            source: Path to PDF file or URL to PDF

        Returns:
            List of quality-validated MCQs
        """
        if pdfplumber is None:
            self.log("pdfplumber not installed. Install with: pip install pdfplumber", 'error')
            return []

        try:
            # Handle URL sources - download to temp file
            if isinstance(source, str) and source.startswith('http'):
                self.log(f"Downloading PDF from: {source}")
                pdf_path = await self._download_pdf(source)
                source_name = source
            else:
                # Handle local file
                pdf_path = Path(source)
                if not pdf_path.exists():
                    self.log(f"PDF file not found: {pdf_path}", 'error')
                    return []
                source_name = pdf_path.name

            self.log(f"Extracting from PDF: {source_name}")

            # 1. Extract all text from PDF
            full_text = self._extract_text_from_pdf(pdf_path)

            if not full_text or len(full_text.strip()) < 50:
                self.log(f"No meaningful text extracted from {source_name}", 'warning')
                return []

            # 2. Quick check: try regex extraction for perfectly structured MCQs (fast, no API call)
            regex_mcqs = self._parse_mcq_text(full_text, str(source))

            if regex_mcqs:
                # Validate regex-extracted MCQs
                passed, failed, stats = self.validator.batch_validate(regex_mcqs)
                self.log(f"Regex extraction: {len(passed)}/{len(regex_mcqs)} passed quality check "
                        f"({stats['pass_rate']*100:.1f}%)")

                # If pass rate is good (>80%), return them
                if stats['pass_rate'] >= 0.8:
                    return passed

                # Otherwise, fall through to LLM extraction for better quality
                self.log("Regex quality insufficient, falling back to LLM extraction for upgrade...")

            # 3. LLM-first approach: send raw text to LLM for intelligent extraction
            if self.llm_client:
                self.log("Using LLM for MAANG-level extraction with quality validation...")
                mcqs = await self._llm_extract(full_text, str(source))
                self.log(f"Extracted {len(mcqs)} quality-validated MCQs from {source_name}")
                return mcqs
            else:
                self.log("No LLM client available for smart extraction", 'warning')
                return []

        except Exception as e:
            self.log(f"Error extracting from PDF {source}: {e}", 'error')
            return []

    async def _download_pdf(self, url: str) -> Path:
        """Download PDF from URL to temporary file."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download PDF: HTTP {response.status}")

                # Create temp file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_path = Path(temp_file.name)

                # Write PDF content
                content = await response.read()
                temp_path.write_bytes(content)

                return temp_path

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract all text from PDF."""
        full_text = ""

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

        return full_text

    async def _llm_extract(self, text: str, source: str) -> List[MCQ]:
        """
        LLM-based extraction with category distribution and quality validation.

        Important: This handles BOTH:
        1. Extracting existing MCQs/Q&As from source
        2. Upgrading quality to meet MAANG standards
        3. Enforcing 50/25/25 distribution

        Args:
            text: Full extracted text from PDF
            source: Source file path

        Returns:
            List of quality-validated MCQ objects
        """
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

    async def _extract_batch_with_distribution(self, text: str, source: str) -> List[MCQ]:
        """
        Extract MCQs from batch with lightweight prompt (no few-shot to avoid 413 errors).

        This method:
        1. Uses minimal, lightweight extraction prompt
        2. Generates with 50/25/25 distribution
        3. Skips few-shot examples to stay under Groq API limits

        Args:
            text: Text batch (~1500 chars after splitting)
            source: Source file path

        Returns:
            List of MCQ objects with distribution enforced
        """
        # Estimate how many questions this batch can yield
        estimated_questions = max(2, len(text) // 400)  # ~1 question per 400 chars

        # Calculate distribution (50/25/25)
        num_conceptual = int(estimated_questions * 0.5)
        num_mathematical = int(estimated_questions * 0.25)
        num_application = estimated_questions - num_conceptual - num_mathematical

        all_mcqs = []

        # Generate for each category with lightweight prompt
        for category, target_count in [
            ('Conceptual', num_conceptual),
            ('Mathematical', num_mathematical),
            ('Application', num_application)
        ]:
            if target_count == 0:
                continue

            # Use lightweight prompt without few-shot examples
            prompt = self._get_lightweight_prompt(category, text, target_count)

            # Call LLM with retry
            response = await self._call_llm_with_retry(prompt)
            if not response:
                continue

            # Parse JSON response
            mcqs_data = self._parse_llm_response(response)

            # Limit to target count
            mcqs_data = mcqs_data[:target_count]

            # Create MCQ objects with answer shuffling
            for data in mcqs_data:
                # Ensure category matches what was requested
                data['category'] = category
                mcq = self._create_mcq_with_shuffle(data, source)
                if mcq:
                    all_mcqs.append(mcq)

        return all_mcqs

    def _get_lightweight_prompt(self, category: str, content: str, target_count: int) -> str:
        """
        Generate lightweight extraction prompt without few-shot examples.
        Avoids 413 Payload Too Large errors by minimizing prompt size.
        """
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
        """
        Call LLM with exponential backoff retry for rate limits.
        Supports both Gemini and OpenAI-compatible APIs.

        Args:
            prompt: Prompt to send to LLM
            max_retries: Maximum number of retry attempts

        Returns:
            LLM response text, or None if all retries fail
        """
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
        """
        Create MCQ from LLM response data with code-level answer randomization.

        Args:
            data: Dictionary with MCQ fields from LLM
            source: Source file path

        Returns:
            MCQ object with shuffled answer positions, or None
        """
        try:
            import uuid
            from datetime import datetime

            options = [data['option_a'], data['option_b'], data['option_c'], data['option_d']]
            correct_letter = data['correct_answer'].strip().upper()

            if correct_letter not in ['A', 'B', 'C', 'D']:
                self.log(f"Invalid correct_answer '{correct_letter}', skipping", 'warning')
                return None

            correct_idx = ord(correct_letter) - ord('A')
            correct_text = options[correct_idx]

            # Shuffle all options randomly (fixes always-C bias)
            random.shuffle(options)

            # Find where the correct answer landed after shuffle
            new_correct_idx = options.index(correct_text)
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
        """
        Split text into LLM-friendly batches without breaking content.

        Args:
            text: Full text to split
            max_chars: Maximum characters per batch (default 4000 for local models)

        Returns:
            List of text batches
        """
        if len(text) <= max_chars:
            return [text]

        # Split by double newlines first, fall back to single newlines
        paragraphs = text.split('\n\n')
        if len(paragraphs) < 3:
            # PDF likely uses single newlines — split on those instead
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
        """
        Parse LLM JSON response with robust cleanup for local models.
        Handles malformed JSON (missing commas, trailing commas, etc.)

        Args:
            response_text: Raw LLM response

        Returns:
            List of MCQ dictionaries with validated fields
        """
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
                # Fix common JSON issues from local models
                # 1. Fix missing commas between objects: }{ -> },{
                text = re.sub(r'\}\s*\{', '},{', text)
                # 2. Fix trailing commas before ] or }
                text = re.sub(r',\s*\]', ']', text)
                text = re.sub(r',\s*\}', '}', text)
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    # 3. Last resort: extract individual JSON objects
                    data = self._extract_json_objects(text)

            if not isinstance(data, list):
                data = [data] if isinstance(data, dict) else []

            # Validate each MCQ has required fields
            valid = [item for item in data if isinstance(item, dict) and all(f in item for f in required)]

            if len(valid) < len(data):
                self.log(f"Filtered {len(data) - len(valid)} invalid MCQs (missing fields)", 'warning')

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
        """
        Parse MCQs from extracted text using regex (fast fallback for structured MCQs).
        Only used when text clearly has A) B) C) D) format.
        """
        mcqs = []

        # Check if text has enough MCQ markers to warrant regex extraction
        mcq_markers = ['A)', 'B)', 'C)', 'D)', '(a)', '(b)', '(c)', '(d)']
        marker_count = sum(1 for marker in mcq_markers if marker in text)
        if marker_count < 3:
            return []

        # Pattern 1: Numbered question with (a) (b) (c) (d)
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

        # Pattern 2: Question with A) B) C) D) format
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

        # Try to extract answers if present
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
