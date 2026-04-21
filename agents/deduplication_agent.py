"""
Deduplication agent for removing duplicate MCQs.
"""

from typing import List

from agents.base_agent import BaseAgent
from config.schemas import MCQ
from utils.similarity import calculate_similarity_hash, fuzzy_match
from storage.excel_handler import ExcelHandler


class DeduplicationAgent(BaseAgent):
    """Handles duplicate detection and removal."""

    def __init__(self, config: dict):
        """Initialize deduplication agent."""
        super().__init__("DeduplicationAgent", config)

        self.similarity_threshold = config.get('similarity_threshold', 0.85)
        self.excel_handler = ExcelHandler(config['excel_path'])

    async def execute(self, mcqs: List[MCQ]) -> List[MCQ]:
        """
        Remove duplicates from MCQ list.

        Strategy:
        1. Load existing MCQs from knowledge base
        2. Calculate hashes for all MCQs
        3. Check exact matches
        4. Check fuzzy matches

        Args:
            mcqs: List of MCQs to deduplicate

        Returns:
            List of unique MCQs
        """
        if not mcqs:
            return mcqs

        self.log_action(f"Deduplicating {len(mcqs)} MCQs")

        # Load existing MCQs
        existing_mcqs = self.excel_handler.load_all_mcqs()
        self.log_action(f"Loaded {len(existing_mcqs)} existing MCQs from knowledge base")

        # Calculate hashes for new MCQs
        for mcq in mcqs:
            mcq.hash_value = calculate_similarity_hash(mcq.question_text)

        # Build hash set from existing MCQs
        existing_hashes = {calculate_similarity_hash(mcq.question_text) for mcq in existing_mcqs}

        unique_mcqs = []
        duplicates_found = 0

        for mcq in mcqs:
            # Check exact hash match
            if mcq.hash_value in existing_hashes:
                self.log_action(f"Duplicate found (exact): {mcq.question_id[:8]}...", 'debug')
                duplicates_found += 1
                continue

            # Check fuzzy match against existing
            is_duplicate = False
            for existing_mcq in existing_mcqs:
                similarity = fuzzy_match(mcq.question_text, existing_mcq.question_text)
                if similarity >= self.similarity_threshold:
                    self.log_action(f"Duplicate found (fuzzy {similarity:.2f}): {mcq.question_id[:8]}...", 'debug')
                    duplicates_found += 1
                    is_duplicate = True
                    break

            if is_duplicate:
                continue

            # Check against already processed unique MCQs
            is_duplicate = False
            for unique_mcq in unique_mcqs:
                similarity = fuzzy_match(mcq.question_text, unique_mcq.question_text)
                if similarity >= self.similarity_threshold:
                    duplicates_found += 1
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_mcqs.append(mcq)
                existing_hashes.add(mcq.hash_value)

        self.log_action(f"Deduplication complete: {len(unique_mcqs)} unique, {duplicates_found} duplicates removed")
        return unique_mcqs
