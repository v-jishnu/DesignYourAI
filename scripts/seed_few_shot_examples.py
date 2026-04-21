"""
Seed Knowledge Base with Few-Shot Examples
==========================================
This script adds the 36 gold-standard few-shot examples from
config/few_shot_examples.py to the Excel knowledge base as starter MCQs.

These examples serve dual purposes:
1. Teaching examples for LLM prompt calibration (via few_shot_examples.py)
2. High-quality starter MCQs in the knowledge base (via this script)

Usage:
    python scripts/seed_few_shot_examples.py
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.few_shot_examples import CONCEPTUAL_EXAMPLES, MATHEMATICAL_EXAMPLES, APPLICATION_EXAMPLES
from config.schemas import MCQ
from config.settings import settings
from storage.excel_handler import ExcelHandler
from agents.deduplication_agent import DeduplicationAgent


async def seed_few_shot_examples():
    """Seed knowledge base with few-shot examples as MCQs."""

    print("=" * 70)
    print("SEEDING KNOWLEDGE BASE WITH FEW-SHOT EXAMPLES")
    print("=" * 70)

    # Collect all examples
    all_examples = []
    all_examples.extend(CONCEPTUAL_EXAMPLES)
    all_examples.extend(MATHEMATICAL_EXAMPLES)
    all_examples.extend(APPLICATION_EXAMPLES)

    print(f"\nFound {len(all_examples)} few-shot examples:")
    print(f"  - Conceptual: {len(CONCEPTUAL_EXAMPLES)}")
    print(f"  - Mathematical: {len(MATHEMATICAL_EXAMPLES)}")
    print(f"  - Application: {len(APPLICATION_EXAMPLES)}")

    # Convert to MCQ objects
    mcqs = []
    for example in all_examples:
        mcq = MCQ(
            question_id=str(uuid.uuid4()),
            question_text=example['question'],
            option_a=example['option_a'],
            option_b=example['option_b'],
            option_c=example['option_c'],
            option_d=example['option_d'],
            correct_answer=example['correct_answer'],
            explanation=example['explanation'],
            category=example['category'],
            topic='ML',  # Default topic
            difficulty='Medium',  # All few-shot examples are Medium difficulty
            source='few_shot_examples.py',
            date_added=datetime.now(),
            used_status=False,
            hash_value=None  # Will be computed by deduplication
        )
        mcqs.append(mcq)

    print(f"\nConverted {len(mcqs)} examples to MCQ objects")

    # Deduplicate (in case already seeded)
    print("\nChecking for duplicates...")
    config = settings.get_config()
    dedup_agent = DeduplicationAgent(config)

    unique_mcqs = await dedup_agent.execute(mcqs)

    duplicates_found = len(mcqs) - len(unique_mcqs)

    if duplicates_found > 0:
        print(f"  [WARN] Found {duplicates_found} duplicates (already in knowledge base)")
        print(f"  [OK] {len(unique_mcqs)} new MCQs to add")
    else:
        print(f"  [OK] All {len(unique_mcqs)} MCQs are new")

    # Store in Excel
    if unique_mcqs:
        print("\nStoring MCQs in Excel knowledge base...")
        excel_handler = ExcelHandler(settings.EXCEL_PATH)
        stored_count = excel_handler.append_mcqs(unique_mcqs)

        print(f"  [OK] Stored {stored_count} MCQs")

        # Display summary
        print("\n" + "=" * 70)
        print("SEEDING COMPLETE")
        print("=" * 70)
        print(f"\nKnowledge Base Updated:")
        print(f"  - Location: {settings.EXCEL_PATH}")
        print(f"  - New MCQs Added: {stored_count}")
        print(f"  - Total MCQs: {excel_handler.get_mcq_count()}")

        # Category distribution
        from collections import Counter
        category_counts = Counter(mcq.category for mcq in unique_mcqs)

        print(f"\nCategory Distribution (New MCQs):")
        for category in ['Conceptual', 'Mathematical', 'Application']:
            count = category_counts.get(category, 0)
            pct = (count / len(unique_mcqs) * 100) if unique_mcqs else 0
            print(f"  - {category}: {count} ({pct:.1f}%)")

        print("\n[SUCCESS] Few-shot examples successfully seeded to knowledge base!")
        print("   These MCQs are now available as high-quality starter questions.\n")
    else:
        print("\n[OK] No new MCQs to add (all examples already in knowledge base)")
        print("=" * 70)


if __name__ == '__main__':
    asyncio.run(seed_few_shot_examples())
