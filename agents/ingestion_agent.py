"""
Ingestion agent - main orchestrator for MCQ ingestion workflow.
"""

from typing import List, Union, Dict
from pathlib import Path

from agents.base_agent import BaseAgent
from agents.extraction_agent import ExtractionAgent
from agents.classification_agent import ClassificationAgent
from agents.deduplication_agent import DeduplicationAgent
from agents.storage_agent import StorageAgent


class IngestionAgent(BaseAgent):
    """Orchestrates the entire ingestion workflow."""

    def __init__(self, config: dict):
        """Initialize ingestion agent."""
        super().__init__("IngestionAgent", config)

        # Initialize sub-agents
        self.extraction_agent = ExtractionAgent(config)
        self.classification_agent = ClassificationAgent(config)
        self.deduplication_agent = DeduplicationAgent(config)
        self.storage_agent = StorageAgent(config)

    async def execute(self, sources: List[Union[str, Path]]) -> Dict:
        """
        Main workflow:
        1. Extract MCQs from sources
        2. Classify MCQs
        3. Deduplicate
        4. Store in Excel

        Args:
            sources: List of URLs or file paths

        Returns:
            Dictionary with execution results
        """
        self.log_action("=" * 60)
        self.log_action("STARTING MCQ INGESTION WORKFLOW")
        self.log_action("=" * 60)

        results = {
            'total_extracted': 0,
            'total_classified': 0,
            'duplicates_found': 0,
            'total_stored': 0,
            'errors': [],

            # Quality and distribution metrics
            'quality_stats': {
                'total_validated': 0,
                'passed': 0,
                'failed': 0,
                'pass_rate': 0.0
            },
            'distribution': {
                'Conceptual': 0,
                'Mathematical': 0,
                'Application': 0
            }
        }

        try:
            # Step 1: Extract
            self.log_action("STEP 1: Extraction")
            mcqs = await self.extraction_agent.execute(sources)
            results['total_extracted'] = len(mcqs)

            if not mcqs:
                self.log_action("No MCQs extracted. Stopping workflow.", 'warning')
                return results

            # Step 2: Classify
            self.log_action("STEP 2: Classification")
            classified_mcqs = await self.classification_agent.execute(mcqs)
            results['total_classified'] = len(classified_mcqs)

            # Step 3: Deduplicate
            self.log_action("STEP 3: Deduplication")
            unique_mcqs = await self.deduplication_agent.execute(classified_mcqs)
            results['duplicates_found'] = len(classified_mcqs) - len(unique_mcqs)

            if not unique_mcqs:
                self.log_action("All MCQs were duplicates. Nothing to store.", 'warning')
                return results

            # Step 4: Store
            self.log_action("STEP 4: Storage")
            stored_count = await self.storage_agent.execute(unique_mcqs)
            results['total_stored'] = stored_count

            # Calculate final distribution and quality metrics
            for mcq in unique_mcqs:
                # Track category distribution
                if mcq.category in results['distribution']:
                    results['distribution'][mcq.category] += 1

            # Calculate distribution percentages
            total_mcqs = sum(results['distribution'].values())
            if total_mcqs > 0:
                self.log_action("\nCategory Distribution:")
                for category, count in results['distribution'].items():
                    pct = (count / total_mcqs) * 100
                    self.log_action(f"  - {category}: {count} ({pct:.1f}%)")

            self.log_action("=" * 60)
            self.log_action("INGESTION WORKFLOW COMPLETE")
            self.log_action("=" * 60)

            return results

        except Exception as e:
            self.handle_error(e, "ingestion workflow")
            results['errors'].append(str(e))
            return results
