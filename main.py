"""
Main entry point for MCQ Knowledge Ingestion & Categorization Agent.
"""

import asyncio
import argparse
from pathlib import Path
import sys

from config.settings import Settings, settings
from agents.ingestion_agent import IngestionAgent
from utils.logger import setup_logging


async def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='MCQ Knowledge Ingestion & Categorization Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single sources
  python main.py --sources "https://example.com/mcqs" "data/raw/questions.pdf"

  # Process from batch file
  python main.py --batch sources.txt --target 800

  # sources.txt format (one per line):
  https://site1.com/ai-mcqs
  data/raw/ml_questions.pdf
  data/raw/ds_interview.docx
        """
    )

    parser.add_argument(
        '--sources',
        nargs='+',
        help='Sources to ingest (URLs or file paths)'
    )

    parser.add_argument(
        '--batch',
        help='Batch file with sources (one per line)'
    )

    parser.add_argument(
        '--target',
        type=int,
        default=settings.MIN_MCQ_TARGET,
        help=f'Target number of MCQs (default: {settings.MIN_MCQ_TARGET})'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(settings.LOG_DIR, settings.LOG_LEVEL)

    # Validate settings
    try:
        settings.validate()
    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        print("\nPlease create a .env file with your ANTHROPIC_API_KEY")
        print("   You can copy .env.template to .env and fill in your API key\n")
        sys.exit(1)

    # Collect sources
    sources = []

    if args.sources:
        sources.extend(args.sources)

    if args.batch:
        batch_path = Path(args.batch)
        if batch_path.exists():
            batch_sources = batch_path.read_text().strip().split('\n')
            sources.extend([s.strip() for s in batch_sources if s.strip()])
        else:
            print(f"Batch file not found: {args.batch}")
            sys.exit(1)

    if not sources:
        print("No sources provided. Use --sources or --batch")
        parser.print_help()
        sys.exit(1)

    # Display startup info
    print("\n" + "="*70)
    print("MCQ KNOWLEDGE INGESTION & CATEGORIZATION AGENT")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  - Sources: {len(sources)}")
    print(f"  - Target: {args.target} MCQs")
    print(f"  - LLM Provider: {settings.LLM_PROVIDER}")
    print(f"  - LLM Model: {settings.LLM_MODELS.get(settings.LLM_PROVIDER, 'Unknown')}")
    print(f"  - Similarity Threshold: {settings.SIMILARITY_THRESHOLD}")
    print(f"  - Knowledge Base: {settings.EXCEL_PATH}")
    print(f"\nSources to process:")
    for i, source in enumerate(sources, 1):
        print(f"  {i}. {source}")
    print()

    # Create ingestion agent
    config = settings.get_config()
    ingestion_agent = IngestionAgent(config)

    # Execute ingestion
    print("Starting ingestion workflow...\n")

    try:
        results = await ingestion_agent.execute(sources)

        # Display results
        print("\n" + "="*70)
        print("INGESTION RESULTS")
        print("="*70)
        print(f"\nExtraction:")
        print(f"  - Extracted: {results['total_extracted']} MCQs")
        print(f"  - Classified: {results['total_classified']} MCQs")
        print(f"  - Duplicates Found: {results['duplicates_found']}")
        print(f"  - Stored: {results['total_stored']} MCQs")

        # Display quality metrics if available
        if 'quality_stats' in results and results['quality_stats']['total_validated'] > 0:
            stats = results['quality_stats']
            print(f"\nQuality Validation:")
            print(f"  - Validated: {stats['total_validated']} MCQs")
            print(f"  - Passed: {stats['passed']} ({stats['pass_rate']*100:.1f}%)")
            print(f"  - Failed: {stats['failed']}")

            if stats['pass_rate'] >= 0.9:
                print(f"  ✓ Excellent quality (≥90% pass rate)")
            elif stats['pass_rate'] >= 0.8:
                print(f"  ⚠ Good quality (≥80% pass rate)")
            else:
                print(f"  ✗ Below target quality (<80% pass rate)")

        # Display category distribution if available
        if 'distribution' in results:
            dist = results['distribution']
            total_dist = sum(dist.values())

            if total_dist > 0:
                print(f"\nCategory Distribution:")
                for category in ['Conceptual', 'Mathematical', 'Application']:
                    count = dist.get(category, 0)
                    pct = (count / total_dist * 100) if total_dist > 0 else 0
                    target_pct = {'Conceptual': 50, 'Mathematical': 25, 'Application': 25}.get(category, 33)
                    status = "✓" if abs(pct - target_pct) <= 5 else "⚠"
                    print(f"  {status} {category}: {count} ({pct:.1f}%, target: {target_pct}%)")

        # Progress towards target
        from storage.excel_handler import ExcelHandler
        excel_handler = ExcelHandler(settings.EXCEL_PATH)
        total_count = excel_handler.get_mcq_count()

        print(f"\nKnowledge Base Status:")
        print(f"  - Total MCQs: {total_count}")
        print(f"  - Target: {args.target}")
        print(f"  - Progress: {total_count}/{args.target} ({total_count/args.target*100:.1f}%)")

        if total_count >= args.target:
            print(f"\n✓ Target achieved! Knowledge base has {total_count} MCQs")
        else:
            remaining = args.target - total_count
            print(f"\n→ {remaining} more MCQs needed to reach target")

        print(f"\nKnowledge base saved to: {settings.EXCEL_PATH}")
        print("="*70 + "\n")

        if results['errors']:
            print("\nErrors encountered:")
            for error in results['errors']:
                print(f"  - {error}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
