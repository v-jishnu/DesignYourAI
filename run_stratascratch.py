"""
StrataScratch full ingestion pipeline.

Extracts all technical interview Q&A pairs from StrataScratch,
converts them to MCQs via LLM, classifies, deduplicates, and stores in the KB.

Usage:
    python run_stratascratch.py                  # Extract all, convert to MCQs, store
    python run_stratascratch.py --extract-only    # Just extract Q&A pairs to JSON
    python run_stratascratch.py --limit 20        # Limit to first 20 questions
    python run_stratascratch.py --dry-run         # Extract + show stats, don't store
"""

import asyncio
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Windows event loop fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from extractors.stratascratch_extractor import StrataScratchExtractor
from config.settings import Settings
from config.schemas import MCQ


# Raw Q&A cache file (avoids re-fetching from API on subsequent runs)
QA_CACHE_PATH = Path("data/processed/stratascratch_qa_cache.json")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"logs/stratascratch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        ]
    )


def parse_args():
    parser = argparse.ArgumentParser(description="StrataScratch ingestion pipeline")
    parser.add_argument('--extract-only', action='store_true',
                        help='Only extract Q&A pairs to JSON cache, skip MCQ conversion')
    parser.add_argument('--limit', type=int, default=0,
                        help='Limit number of questions to process (0=all)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Extract and show stats, but do not store in KB')
    parser.add_argument('--use-cache', action='store_true',
                        help='Use cached Q&A pairs instead of re-fetching from API')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Number of Q&A pairs to convert per LLM batch')
    return parser.parse_args()


async def extract_qa_pairs(limit: int = 0) -> list:
    """Extract Q&A pairs from StrataScratch API."""
    config = {
        'stratascratch_token': Settings.STRATASCRATCH_TOKEN,
        'stratascratch_page_size': 50,
        'stratascratch_request_delay': 0.3,
        'stratascratch_job_positions': [1, 11, 2, 4, 5],
        'stratascratch_question_types': [],
        'stratascratch_difficulties': [],
        'stratascratch_companies': [],
        'stratascratch_max_details': limit,
    }

    extractor = StrataScratchExtractor(config)
    mcqs = await extractor.extract("stratascratch")

    # Convert to serializable Q&A pairs with metadata
    qa_pairs = []
    for mcq in mcqs:
        qa_pairs.append({
            'question': mcq.question_text,
            'answer': mcq.explanation or '',
            'difficulty': mcq.difficulty,
            'topic': mcq.topic,
            'company': mcq.company,
            'job_roles': mcq.job_roles,
            'source': mcq.source,
        })

    return qa_pairs


def save_qa_cache(qa_pairs: list):
    """Save Q&A pairs to JSON cache."""
    QA_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QA_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, indent=2, ensure_ascii=False)
    print(f"Cached {len(qa_pairs)} Q&A pairs to {QA_CACHE_PATH}")


def load_qa_cache() -> list:
    """Load Q&A pairs from JSON cache."""
    if not QA_CACHE_PATH.exists():
        print("No cache found. Run without --use-cache first.")
        return []
    with open(QA_CACHE_PATH, 'r', encoding='utf-8') as f:
        qa_pairs = json.load(f)
    print(f"Loaded {len(qa_pairs)} Q&A pairs from cache")
    return qa_pairs


async def convert_and_ingest(qa_pairs: list, dry_run: bool = False, batch_size: int = 10):
    """Convert Q&A pairs to MCQs and run through classification → dedup → storage."""
    from generators.qa_converter import QAConverter
    from agents.deduplication_agent import DeduplicationAgent
    from agents.storage_agent import StorageAgent

    config = Settings.get_config()

    # Initialize LLM client for Q&A conversion
    llm_config = config['llm_config']
    provider = llm_config['provider']

    print(f"\nUsing LLM provider: {provider} (model: {llm_config['model']})")

    if provider == 'gemini':
        from classifiers.gemini_classifier import GeminiClassifier
        llm_client = GeminiClassifier(
            api_key=llm_config['api_key'],
            model=llm_config['model']
        )
    elif provider in ['groq', 'openai', 'together', 'qwen', 'deepseek', 'ollama']:
        from openai import AsyncOpenAI
        base_url = config.get('llm_base_url')
        llm_client = AsyncOpenAI(
            api_key=llm_config['api_key'],
            base_url=base_url
        )
        llm_client.model_name = llm_config['model']
        llm_client.provider = provider
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    converter = QAConverter(llm_client, config, strict_validation=False)

    # Incremental save setup — save every SAVE_EVERY MCQs so progress isn't lost
    SAVE_EVERY = 25
    from storage.excel_handler import ExcelHandler
    excel_handler = ExcelHandler(Settings.EXCEL_PATH)

    # Convert Q&A pairs to MCQs
    print(f"\nConverting {len(qa_pairs)} Q&A pairs to MCQs (saving every {SAVE_EVERY})...")
    print("=" * 60)

    batch_mcqs = []  # current unsaved batch
    total_converted = 0
    total_stored = 0
    failed = 0

    for i, qa in enumerate(qa_pairs, 1):
        print(f"[{i}/{len(qa_pairs)}] Converting: {qa['question'][:70]}...")

        mcq = await converter.convert_qa_to_mcq(
            question=qa['question'],
            answer=qa['answer'],
            source=qa['source'],
        )

        if mcq:
            # Preserve metadata from StrataScratch
            mcq.company = qa.get('company')
            mcq.job_roles = qa.get('job_roles')

            # Use StrataScratch difficulty if classification didn't set it
            if not mcq.difficulty and qa.get('difficulty'):
                mcq.difficulty = qa['difficulty']

            batch_mcqs.append(mcq)
            total_converted += 1
            print(f"  -> {mcq.category} | {mcq.topic} | {mcq.difficulty} | Company: {mcq.company or 'N/A'}")
        else:
            failed += 1
            print(f"  -> FAILED (quality check)")

        # Incremental save
        if not dry_run and len(batch_mcqs) >= SAVE_EVERY:
            saved = excel_handler.append_mcqs(batch_mcqs)
            total_stored += saved
            print(f"  ** Saved batch of {saved} MCQs (total stored: {total_stored}) **")
            batch_mcqs = []

    # Save remaining batch
    if not dry_run and batch_mcqs:
        saved = excel_handler.append_mcqs(batch_mcqs)
        total_stored += saved
        print(f"  ** Saved final batch of {saved} MCQs (total stored: {total_stored}) **")

    print(f"\n{'=' * 60}")
    print(f"Conversion complete: {total_converted} MCQs created, {failed} failed, {total_stored} stored")

    # Final KB count
    total = excel_handler.get_mcq_count()
    print(f"Total MCQs in knowledge base: {total}")


async def main():
    args = parse_args()

    # Ensure directories exist
    Path("logs").mkdir(exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)

    setup_logging()

    print("=" * 60)
    print("StrataScratch Ingestion Pipeline")
    print("=" * 60)

    # Step 1: Get Q&A pairs
    if args.use_cache:
        qa_pairs = load_qa_cache()
    else:
        print(f"\nExtracting Q&A pairs from StrataScratch API...")
        qa_pairs = await extract_qa_pairs(limit=args.limit)
        save_qa_cache(qa_pairs)

    if not qa_pairs:
        print("No Q&A pairs found. Exiting.")
        return

    # Show extraction summary
    print(f"\n--- Extraction Summary ---")
    print(f"Total Q&A pairs: {len(qa_pairs)}")
    difficulties = {}
    companies = {}
    for qa in qa_pairs:
        d = qa.get('difficulty', 'Unknown')
        difficulties[d] = difficulties.get(d, 0) + 1
        c = qa.get('company', 'Unknown')
        if c:
            companies[c] = companies.get(c, 0) + 1

    print(f"Difficulties: {difficulties}")
    print(f"Unique companies: {len(companies)}")
    print(f"Top companies: {dict(sorted(companies.items(), key=lambda x: -x[1])[:10])}")

    if args.extract_only:
        print("\n[Extract-only mode] Q&A pairs cached. Run again without --extract-only to convert.")
        return

    # Apply limit if set
    if args.limit > 0:
        qa_pairs = qa_pairs[:args.limit]

    # Step 2: Convert → Classify → Dedup → Store
    await convert_and_ingest(qa_pairs, dry_run=args.dry_run, batch_size=args.batch_size)


if __name__ == "__main__":
    asyncio.run(main())
