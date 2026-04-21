"""
Q&A-to-MCQ Converter - Converts Q&A pairs to MAANG-level MCQs with quality validation.

This module transforms Q&A pairs into high-quality MCQs:
1. Auto-detects appropriate category (Conceptual/Mathematical/Application)
2. Uses category-specific MAANG prompts with few-shot examples
3. Upgrades shallow questions to reasoning-based questions
4. Validates quality through 5-point checklist
5. Retries with upgrade instructions if quality check fails
"""

import json
import logging
import random
import asyncio
import uuid
from typing import Optional

from config.schemas import MCQ
from classifiers.prompt_templates import get_maang_prompt
from validators.quality_validator import QualityValidator


class QAConverter:
    """Convert descriptive Q&A pairs to MCQ format using LLM."""

    def __init__(self, llm_client, config, strict_validation: bool = True):
        """
        Initialize QA Converter with quality validation.

        Args:
            llm_client: LLM client (GeminiClassifier) for generating distractors
            config: Configuration dictionary
            strict_validation: If False, relaxes quality checks for pre-vetted sources
        """
        self.llm_client = llm_client
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.validator = QualityValidator()
        self.strict_validation = strict_validation

    async def convert_qa_to_mcq(self, question: str, answer: str, source: str, category: str = None) -> Optional[MCQ]:
        """
        Convert Q&A pair to MAANG-level MCQ with quality validation and upgrade.

        Args:
            question: Question text
            answer: Correct answer text
            source: Source file/URL
            category: Optional category hint (auto-detect if None)

        Returns:
            Quality-validated MCQ object, or None if conversion/validation fails
        """
        max_retries = 3

        # Auto-detect category if not provided
        if not category:
            category = self._detect_category(question, answer)

        for attempt in range(max_retries):
            try:
                self.logger.info(f"Converting Q&A to MAANG {category} MCQ: {question[:60]}...")

                # Use category-specific MAANG prompt with few-shot examples
                content_block = f"Question: {question}\nAnswer: {answer}"
                prompt = get_maang_prompt(category, content_block)

                # Call LLM with retry for rate limiting
                response = await self._call_llm_with_retry(prompt)
                if not response:
                    continue

                # Parse response (expects JSON array, take first MCQ)
                mcqs_data = self._parse_llm_response(response)
                if not mcqs_data:
                    self.logger.warning("No valid MCQs in LLM response")
                    continue

                mcq_data = mcqs_data[0]

                # Ensure category matches what was requested
                mcq_data['category'] = category

                # Create MCQ object with answer shuffling
                mcq = self._create_mcq_with_shuffle(mcq_data, source)
                if not mcq:
                    continue

                # Validate quality
                is_valid, reason, checks = self.validator.validate_mcq(mcq, strict=self.strict_validation)

                if is_valid:
                    self.logger.info(f"Q&A converted to MAANG-level MCQ (category: {mcq.category})")
                    return mcq
                else:
                    self.logger.warning(f"Q&A conversion failed quality check: {reason}")

                    # If failed and we have retries left, try again
                    if attempt < max_retries - 1:
                        self.logger.info(f"Retrying with quality focus (attempt {attempt+2}/{max_retries})")
                        continue
                    else:
                        self.logger.error(f"Failed to generate quality MCQ after {max_retries} attempts")
                        return None

            except Exception as e:
                error_str = str(e)
                if '429' in error_str and attempt < max_retries - 1:
                    wait_time = 60 * (attempt + 1)
                    self.logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"Error converting Q&A to MCQ: {e}")
                    self.logger.debug(f"Question: {question[:100]}")
                    self.logger.debug(f"Answer: {answer[:100]}")
                    if attempt == max_retries - 1:
                        return None

        return None

    def _detect_category(self, question: str, answer: str) -> str:
        """
        Auto-detect MCQ category from Q&A content.

        Heuristics:
        - Mathematical: Contains formulas, numbers, equations, probability terms
        - Application: Contains scenario words (production, deployment, A/B test, metrics)
        - Conceptual: Default (trade-offs, comparisons, "why", "when")

        Args:
            question: Question text
            answer: Answer text

        Returns:
            Detected category ('Mathematical', 'Application', or 'Conceptual')
        """
        combined = (question + " " + answer).lower()

        # Mathematical signals
        math_keywords = ['formula', 'equation', 'probability', 'calculate', 'derivative',
                        'gradient', 'matrix', 'vector', 'variance', 'mean', 'std', 'eigenvalue',
                        'covariance', 'distribution', 'integral', 'optimization', 'converge']

        # Application signals
        app_keywords = ['production', 'deployment', 'a/b test', 'metric', 'pipeline',
                       'monitoring', 'scenario', 'real-world', 'system', 'latency',
                       'performance', 'scale', 'infrastructure', 'api', 'service']

        # Count keyword occurrences
        math_count = sum(1 for kw in math_keywords if kw in combined)
        app_count = sum(1 for kw in app_keywords if kw in combined)

        # Decide category based on strongest signal
        if math_count >= 2:
            return 'Mathematical'
        elif app_count >= 2:
            return 'Application'
        else:
            return 'Conceptual'

    async def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        Call LLM with exponential backoff retry for rate limiting.
        Supports both Gemini and OpenAI-compatible APIs (Groq, DeepSeek, Ollama, etc.).

        Args:
            prompt: The prompt to send
            max_retries: Maximum number of retry attempts

        Returns:
            Response text from LLM, or None if all retries fail
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
                    if attempt < max_retries - 1:
                        wait_time = min(60 * (attempt + 1), 120)  # 60s, 120s
                        self.logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                    else:
                        self.logger.error(f"Failed after {max_retries} retries due to rate limiting")
                        return None
                else:
                    # Non-rate-limit error, don't retry
                    self.logger.error(f"LLM call error: {e}")
                    return None

        return None

    def _parse_llm_response(self, response_text: str) -> list:
        """
        Parse LLM JSON response (expects array format from MAANG prompts).

        Args:
            response_text: Raw LLM response

        Returns:
            List of MCQ dictionaries with validated fields
        """
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

            # Fix invalid JSON escapes (e.g. \beta, \alpha from LaTeX)
            # Replace invalid \X sequences with \\X so JSON parser accepts them
            import re
            text = re.sub(r'\\([^"\\/bfnrtu])', r'\\\\\1', text)

            data = json.loads(text)

            if not isinstance(data, list):
                self.logger.warning("LLM response is not a JSON array, wrapping in array")
                data = [data]

            # Validate each MCQ has required fields
            required = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
            valid = [item for item in data if all(f in item for f in required)]

            if len(valid) < len(data):
                self.logger.warning(f"Filtered {len(data) - len(valid)} invalid MCQs (missing fields)")

            return valid

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM JSON response: {e}")
            self.logger.debug(f"Response text: {response_text[:500]}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {e}")
            return []

    def _create_mcq_with_shuffle(self, data: dict, source: str) -> Optional[MCQ]:
        """
        Create MCQ from LLM response data with answer randomization.

        Args:
            data: Dictionary with MCQ fields from LLM
            source: Source file path

        Returns:
            MCQ object with shuffled answer positions, or None if validation fails
        """
        try:
            from datetime import datetime

            options = [data['option_a'], data['option_b'], data['option_c'], data['option_d']]
            correct_letter = data['correct_answer'].strip().upper()

            if correct_letter not in ['A', 'B', 'C', 'D']:
                self.logger.warning(f"Invalid correct_answer '{correct_letter}', skipping")
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
                topic=data.get('topic', 'AI'),
                difficulty=data.get('difficulty', 'Medium'),
                source=source,
                date_added=datetime.now(),
                used_status=False,
                hash_value=None  # Will be computed by deduplication agent
            )

            return mcq

        except Exception as e:
            self.logger.error(f"Error creating MCQ: {e}")
            return None

    async def convert_batch(self, qa_pairs: list, source: str, max_conversions: int = 50) -> list:
        """
        Convert multiple Q&A pairs to MAANG-level MCQs with quality validation.

        Args:
            qa_pairs: List of dicts with 'question' and 'answer' keys
            source: Source file/URL
            max_conversions: Maximum number of conversions to perform

        Returns:
            List of quality-validated MCQ objects
        """
        converted_mcqs = []

        # Limit conversions to avoid excessive LLM calls
        qa_pairs_to_convert = qa_pairs[:max_conversions]

        if len(qa_pairs) > max_conversions:
            self.logger.warning(
                f"Limiting Q&A conversions to {max_conversions} (found {len(qa_pairs)} Q&A pairs)"
            )

        for i, qa_pair in enumerate(qa_pairs_to_convert, 1):
            self.logger.info(f"Converting Q&A {i}/{len(qa_pairs_to_convert)} to MAANG-level MCQ...")

            mcq = await self.convert_qa_to_mcq(
                question=qa_pair['question'],
                answer=qa_pair['answer'],
                source=source
            )

            if mcq:
                converted_mcqs.append(mcq)
            else:
                self.logger.warning(f"Failed to convert Q&A {i} (quality check failed), skipping")

        # Calculate pass rate
        pass_rate = len(converted_mcqs) / len(qa_pairs_to_convert) if qa_pairs_to_convert else 0
        self.logger.info(f"Converted {len(converted_mcqs)}/{len(qa_pairs_to_convert)} Q&A pairs to quality MCQs ({pass_rate*100:.1f}% success rate)")

        return converted_mcqs
