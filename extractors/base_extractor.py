"""
Base extractor class for all content extractors.
"""

from abc import ABC, abstractmethod
from typing import List, Union, Optional
from pathlib import Path
import logging

from config.schemas import MCQ


class BaseExtractor(ABC):
    """Abstract base class for all extractors."""

    def __init__(self, config: dict, media_handler=None, llm_client=None):
        """
        Initialize base extractor.

        Args:
            config: Configuration dictionary
            media_handler: Optional MediaHandler for image extraction
            llm_client: Optional LLM client for content generation
        """
        self.config = config
        self.media_handler = media_handler
        self.llm_client = llm_client
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def extract(self, source: Union[str, Path]) -> List[MCQ]:
        """
        Extract MCQs from source.

        Args:
            source: URL or file path

        Returns:
            List of extracted MCQs
        """
        pass

    def log(self, message: str, level: str = 'info'):
        """Log message."""
        getattr(self.logger, level)(message)

    def _create_mcq(
        self,
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        source: str,
        correct_answer: str = None,
        explanation: str = None
    ) -> MCQ:
        """
        Create MCQ object with validation.

        Args:
            question_text: Question text
            option_a: Option A
            option_b: Option B
            option_c: Option C
            option_d: Option D
            source: Source URL or file path
            correct_answer: Correct answer (A/B/C/D)
            explanation: Explanation text

        Returns:
            MCQ object if valid, None otherwise
        """
        from utils.text_processor import clean_text

        # Clean all text fields
        question_text = clean_text(question_text) if question_text else ""
        option_a = clean_text(option_a) if option_a else ""
        option_b = clean_text(option_b) if option_b else ""
        option_c = clean_text(option_c) if option_c else ""
        option_d = clean_text(option_d) if option_d else ""
        explanation = clean_text(explanation) if explanation else None

        # Validate required fields
        if not all([question_text, option_a, option_b, option_c, option_d]):
            self.log(f"Skipping invalid MCQ (missing fields): {question_text[:50]}...", 'warning')
            return None

        try:
            mcq = MCQ(
                question_text=question_text,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                source=str(source),
                correct_answer=correct_answer,
                explanation=explanation
            )

            return mcq if mcq.is_valid() else None

        except Exception as e:
            self.log(f"Error creating MCQ: {e}", 'error')
            return None
