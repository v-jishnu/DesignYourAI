"""
Data validation for MCQ schema.
"""

from config.schemas import MCQ
import logging


class DataValidator:
    """Validate MCQ data against schema."""

    def __init__(self):
        """Initialize validator."""
        self.logger = logging.getLogger(__name__)

    def validate(self, mcq: MCQ) -> bool:
        """
        Validate MCQ object.

        Args:
            mcq: MCQ object to validate

        Returns:
            True if valid, False otherwise
        """
        # Use built-in validation
        if not mcq.is_valid():
            self.logger.warning(f"MCQ validation failed: {mcq.question_id}")
            return False

        # Additional validations
        if mcq.category and mcq.category not in ['Conceptual', 'Mathematical', 'Application']:
            self.logger.warning(f"Invalid category: {mcq.category}")
            return False

        if mcq.topic and mcq.topic not in ['AI', 'ML', 'Data Science', 'System Design']:
            self.logger.warning(f"Invalid topic: {mcq.topic}")
            return False

        if mcq.difficulty and mcq.difficulty not in ['Easy', 'Medium', 'Hard']:
            self.logger.warning(f"Invalid difficulty: {mcq.difficulty}")
            return False

        if mcq.correct_answer and mcq.correct_answer not in ['A', 'B', 'C', 'D']:
            self.logger.warning(f"Invalid correct answer: {mcq.correct_answer}")
            return False

        return True
