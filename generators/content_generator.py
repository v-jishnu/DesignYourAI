"""
Content-to-MCQ generator using LLM.

Generates MAANG-level MCQs from any educational content with quality validation.
"""

import asyncio
import json
import logging
import random
import re
from typing import List, Tuple
from config.schemas import MCQ
from classifiers.prompt_templates import get_maang_prompt
from validators.quality_validator import QualityValidator


class ContentGenerator:
    """Generate MAANG-level MCQs from educational content using LLM."""

    def __init__(self, llm_client, config: dict):
        """
        Initialize content generator.

        Args:
            llm_client: LLM client (GeminiClassifier, Claude, OpenAI, etc.)
            config: Configuration dict with generation settings
        """
        self.llm_client = llm_client
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.validator = QualityValidator()

    async def generate_from_content(self, content: str, source: str,
                                   num_questions: int = 5) -> List[MCQ]:
        """
        Generate MCQs from content with 50/25/25 distribution and quality validation.

        Args:
            content: Text content (article, tutorial, documentation)
            source: Source URL/path for tracking
            num_questions: Number of MCQs to generate (default: 5)

        Returns:
            List of quality-validated MCQs with enforced distribution
        """
        self.logger.info(f"Generating {num_questions} MCQs from content ({len(content)} chars)")

        # Check content length
        min_length = self.config.get('generation_min_content_length', 500)
        if len(content.split()) < min_length:
            self.logger.warning(f"Content too short ({len(content.split())} words < {min_length})")
            return []

        # Calculate distribution targets (50/25/25)
        num_conceptual = int(num_questions * 0.5)  # 50%
        num_mathematical = int(num_questions * 0.25)  # 25%
        num_application = num_questions - num_conceptual - num_mathematical  # 25%

        self.logger.info(f"Target distribution: Conceptual={num_conceptual}, "
                        f"Mathematical={num_mathematical}, Application={num_application}")

        all_mcqs = []

        # Generate each category separately with category-specific prompts
        categories = [
            ('Conceptual', num_conceptual),
            ('Mathematical', num_mathematical),
            ('Application', num_application)
        ]

        for category, target_count in categories:
            if target_count == 0:
                continue

            self.logger.info(f"Generating {target_count} {category} questions...")

            # Generate with category-specific prompt and quality validation
            mcqs = await self._generate_category_mcqs(content, source, category, target_count)

            # Validate quality
            if mcqs:
                passed, failed, stats = self.validator.batch_validate(mcqs)

                if stats['pass_rate'] < 0.9:
                    self.logger.warning(f"{category}: {stats['pass_rate']*100:.1f}% pass rate (target: 90%)")

                # Log first failure for debugging
                if failed:
                    mcq, reason = failed[0]
                    self.logger.debug(f"Quality fail example: {mcq.question_text[:60]}... | {reason}")

                all_mcqs.extend(passed)
                self.logger.info(f"{category}: {len(passed)}/{len(mcqs)} passed quality validation")

        self.logger.info(f"Generated {len(all_mcqs)} validated MCQs with distribution: "
                        f"Conceptual={sum(1 for m in all_mcqs if m.category=='Conceptual')}, "
                        f"Math={sum(1 for m in all_mcqs if m.category=='Mathematical')}, "
                        f"App={sum(1 for m in all_mcqs if m.category=='Application')}")

        return all_mcqs

    def _segment_content(self, content: str) -> List[str]:
        """
        Segment content into topic chunks for generation.

        Strategy:
        - If content <= 4000 chars: Single segment
        - If content > 4000 chars: Split by paragraphs, create 3-4 segments

        Args:
            content: Full text content

        Returns:
            List of content segments (each 300-800 words optimal)
        """
        max_length = self.config.get('generation_max_content_length', 4000)

        # If short enough, return as single segment
        if len(content) <= max_length:
            return [content]

        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\n+', content)

        # Build segments of ~4000 chars each
        segments = []
        current_segment = []
        current_length = 0

        for para in paragraphs:
            para_length = len(para)

            # If adding this paragraph exceeds max, start new segment
            if current_length + para_length > max_length and current_segment:
                segments.append('\n\n'.join(current_segment))
                current_segment = [para]
                current_length = para_length
            else:
                current_segment.append(para)
                current_length += para_length

        # Add final segment
        if current_segment:
            segments.append('\n\n'.join(current_segment))

        # Limit to first 3 segments (avoid generating too many MCQs)
        return segments[:3]

    async def _generate_category_mcqs(self, content: str, source: str,
                                     category: str, target_count: int) -> List[MCQ]:
        """
        Generate MCQs for a specific category using category-specific MAANG prompts.

        Args:
            content: Full content text
            source: Source URL/path
            category: 'Conceptual', 'Mathematical', or 'Application'
            target_count: Number of MCQs to generate for this category

        Returns:
            List of generated MCQ objects
        """
        try:
            # Use category-specific MAANG prompt with few-shot examples
            prompt = get_maang_prompt(category, content)

            # Call LLM with retry logic for rate limiting
            response = await self._call_llm_with_retry(prompt, max_retries=3)

            # Parse JSON response
            mcqs_data = self._parse_generation_response(response)

            # Limit to target count
            mcqs_data = mcqs_data[:target_count]

            # Create MCQ objects with answer shuffling
            mcqs = []
            for data in mcqs_data:
                # Ensure category matches what was requested
                data['category'] = category
                mcq = self._create_mcq(data, source)
                if mcq:
                    mcqs.append(mcq)

            self.logger.info(f"Generated {len(mcqs)} {category} MCQs")
            return mcqs

        except Exception as e:
            self.logger.error(f"Error generating {category} MCQs: {e}")
            return []

    async def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call LLM with exponential backoff retry for rate limiting.
        Supports both Gemini and OpenAI-compatible APIs (Groq, DeepSeek, Ollama, etc.).

        Args:
            prompt: The prompt to send
            max_retries: Maximum number of retry attempts

        Returns:
            Response text from LLM

        Raises:
            Exception if all retries fail
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
                    # OpenAI-compatible API (Groq, OpenAI, Together, DeepSeek, Ollama)
                    response = await self.llm_client.chat.completions.create(
                        model=self.llm_client.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7
                    )
                    return response.choices[0].message.content

            except Exception as e:
                error_str = str(e)

                # Check if rate limited (429 error)
                if '429' in error_str or 'rate' in error_str.lower():
                    wait_time = min(60 * (attempt + 1), 120)  # 60s, 120s
                    self.logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    # Non-rate-limit error, don't retry
                    raise

        raise Exception(f"Failed after {max_retries} retries due to rate limiting")

    def _parse_generation_response(self, response_text: str) -> List[dict]:
        """
        Parse LLM response into structured MCQ data.

        Handles:
        - Markdown code blocks (```json)
        - Extra text before/after JSON
        - Validation of required fields

        Args:
            response_text: Raw LLM response

        Returns:
            List of MCQ dictionaries
        """
        try:
            # Remove markdown code blocks if present
            response_text = response_text.strip()

            # Remove ```json or ``` markers
            if response_text.startswith('```'):
                lines = response_text.split('\n')

                # Find start and end of JSON
                start_idx = 0
                end_idx = len(lines)

                for i, line in enumerate(lines):
                    if line.strip().startswith('['):
                        start_idx = i
                        break

                for i in range(len(lines)-1, -1, -1):
                    if lines[i].strip().endswith(']'):
                        end_idx = i + 1
                        break

                response_text = '\n'.join(lines[start_idx:end_idx])

            response_text = response_text.strip()

            # Parse JSON
            mcqs_data = json.loads(response_text)

            # Validate structure
            if not isinstance(mcqs_data, list):
                raise ValueError("Response is not a list")

            # Validate each MCQ has required fields
            required_fields = ['question_text', 'option_a', 'option_b',
                             'option_c', 'option_d', 'correct_answer', 'category']

            valid_mcqs = []
            for item in mcqs_data:
                if all(field in item for field in required_fields):
                    valid_mcqs.append(item)
                else:
                    self.logger.warning(f"Skipping invalid MCQ (missing fields): {item.keys()}")

            return valid_mcqs

        except Exception as e:
            self.logger.error(f"Error parsing generation response: {e}")
            self.logger.debug(f"Response text: {response_text[:500]}")
            return []

    def _create_mcq(self, data: dict, source: str) -> MCQ:
        """
        Create MCQ object from generated data.

        Args:
            data: Dictionary with MCQ fields
            source: Source URL/path

        Returns:
            MCQ object or None if validation fails
        """
        try:
            # Generate unique ID
            import uuid
            question_id = str(uuid.uuid4())[:8]

            # Validate correct_answer format
            correct_answer = data['correct_answer'].strip().upper()
            if correct_answer not in ['A', 'B', 'C', 'D']:
                self.logger.warning(f"Invalid correct_answer: {correct_answer}, skipping MCQ")
                return None

            # Validate category
            category = data.get('category', 'Conceptual')
            if category not in ['Mathematical', 'Application', 'Conceptual']:
                self.logger.warning(f"Invalid category: {category}, defaulting to Conceptual")
                category = 'Conceptual'

            # Shuffle answer positions in code (fixes always-C LLM bias)
            options = [data['option_a'].strip(), data['option_b'].strip(),
                       data['option_c'].strip(), data['option_d'].strip()]
            correct_idx = ord(correct_answer) - ord('A')
            correct_text = options[correct_idx]

            random.shuffle(options)

            new_correct_idx = options.index(correct_text)
            correct_answer = chr(ord('A') + new_correct_idx)

            # Create MCQ
            from datetime import datetime

            mcq = MCQ(
                question_id=question_id,
                question_text=data['question_text'].strip(),
                option_a=options[0],
                option_b=options[1],
                option_c=options[2],
                option_d=options[3],
                correct_answer=correct_answer,
                explanation=data.get('explanation', '').strip(),
                category=category,
                topic=data.get('topic', 'AI'),  # Default topic
                difficulty=data.get('difficulty', 'Medium'),  # Default difficulty
                source=source,
                date_added=datetime.now(),
                used_status=False,
                hash_value=None  # Will be computed by deduplication agent
            )

            return mcq

        except Exception as e:
            self.logger.error(f"Error creating MCQ from data: {e}")
            return None

