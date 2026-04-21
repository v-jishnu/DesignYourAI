"""
Storage agent for managing Excel operations.
"""

from typing import List

from agents.base_agent import BaseAgent
from config.schemas import MCQ
from storage.excel_handler import ExcelHandler
from storage.data_validator import DataValidator


class StorageAgent(BaseAgent):
    """Manages Excel storage operations."""

    def __init__(self, config: dict):
        """Initialize storage agent."""
        super().__init__("StorageAgent", config)

        self.excel_handler = ExcelHandler(config['excel_path'])
        self.validator = DataValidator()

    async def execute(self, mcqs: List[MCQ]) -> int:
        """
        Store MCQs in Excel knowledge base.

        Args:
            mcqs: List of MCQs to store

        Returns:
            Number of MCQs successfully stored
        """
        if not mcqs:
            return 0

        self.log_action(f"Validating {len(mcqs)} MCQs")

        # Validate all MCQs
        validated_mcqs = []
        for mcq in mcqs:
            if self.validator.validate(mcq):
                validated_mcqs.append(mcq)
            else:
                self.log_action(f"Validation failed for MCQ: {mcq.question_id[:8]}...", 'warning')

        self.log_action(f"{len(validated_mcqs)} MCQs passed validation")

        # Store to Excel
        try:
            stored_count = self.excel_handler.append_mcqs(validated_mcqs)
            self.log_action(f"Stored {stored_count} MCQs to Excel")

            # Log final count
            total_count = self.excel_handler.get_mcq_count()
            self.log_action(f"Total MCQs in knowledge base: {total_count}")

            return stored_count

        except Exception as e:
            self.handle_error(e, "Excel storage")
            return 0
