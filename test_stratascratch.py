"""
Quick test for StrataScratch extractor.
Fetches a small batch of questions to verify API connectivity and data extraction.

Usage:
    python test_stratascratch.py           # Test with 5 questions
    python test_stratascratch.py --all     # Fetch all questions (takes a few minutes)
"""

import asyncio
import sys

# Windows event loop fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from extractors.stratascratch_extractor import StrataScratchExtractor


async def test_extract(max_details: int = 5):
    """Test fetching questions from StrataScratch."""
    config = {
        'stratascratch_token': 'b38322ffb1e36d79fb233b1b34a6cb288e2611f9',
        'stratascratch_page_size': 50,
        'stratascratch_request_delay': 0.3,
        'stratascratch_job_positions': [1, 11, 2, 4, 5],
        'stratascratch_question_types': [],
        'stratascratch_difficulties': [],
        'stratascratch_companies': [],
        'stratascratch_max_details': max_details,
    }

    extractor = StrataScratchExtractor(config)

    print("=" * 60)
    print(f"Testing StrataScratch Extractor (max_details={max_details})")
    print("=" * 60)

    mcqs = await extractor.extract("stratascratch")

    print(f"\nFetched {len(mcqs)} Q&A pairs\n")

    for i, mcq in enumerate(mcqs[:3], 1):
        print(f"--- Question {i} ---")
        print(f"Q: {mcq.question_text[:150]}...")
        print(f"Difficulty: {mcq.difficulty}")
        print(f"Topic: {mcq.topic}")
        print(f"Source: {mcq.source}")
        if mcq.explanation:
            print(f"Answer preview: {mcq.explanation[:150]}...")
        print()

    qa_pairs = extractor.get_qa_pairs(mcqs)
    print(f"Ready for Q&A-to-MCQ conversion: {len(qa_pairs)} pairs")


if __name__ == "__main__":
    max_details = 5
    if '--all' in sys.argv:
        max_details = 0  # 0 = no limit
    asyncio.run(test_extract(max_details))
