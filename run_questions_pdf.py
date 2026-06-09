"""
Generate MCQs from a questions-only PDF.

Reads bare questions from a PDF (no options present), calls the LLM to generate
4 options, the correct answer, an explanation, and classifies each question by
category/topic/difficulty.  Output is a standard KB Excel file ready to use
(or pass through the eval pipeline with run_eval.py --fix).

Examples:
    python run_questions_pdf.py --pdf questions.pdf
    python run_questions_pdf.py --pdf questions.pdf --output my_kb.xlsx
    python run_questions_pdf.py --pdf questions.pdf --concurrency 4 --verbose
"""

import argparse
import asyncio
import sys
from pathlib import Path

import pandas as pd

from config.settings import settings
from utils.logger import setup_logging


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate MCQs from a questions-only PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--pdf", required=True, help="Path to the PDF with bare questions.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output Excel path (default: <pdf_name>_generated_kb.xlsx next to the PDF).",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        metavar="N",
        help="Max concurrent LLM calls (default: 2 for Ollama; raise to 6+ for API providers).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each question as it is processed.",
    )
    return parser.parse_args()


async def _main() -> int:
    args = _parse_args()
    setup_logging(settings.LOG_DIR, settings.LOG_LEVEL)

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"\nError: PDF not found: {pdf_path}\n")
        return 1

    out_path = Path(args.output) if args.output else (
        pdf_path.parent / (pdf_path.stem + "_generated_kb.xlsx")
    )

    # Build LLM client (same factory used by ExtractionAgent)
    config = settings.get_config() if hasattr(settings, "get_config") else {}
    llm_config = config.get("llm_config", {})
    provider = llm_config.get("provider", "gemini")

    try:
        if provider == "gemini":
            from classifiers.gemini_classifier import GeminiClassifier
            llm_client = GeminiClassifier(
                api_key=llm_config["api_key"],
                model=llm_config["model"],
            )
        elif provider in ("groq", "openai", "together", "qwen", "deepseek", "ollama"):
            from openai import AsyncOpenAI
            llm_client = AsyncOpenAI(
                api_key=llm_config["api_key"],
                base_url=config.get("llm_base_url"),
            )
            llm_client.model_name = llm_config["model"]
            llm_client.provider = provider
        else:
            print(f"\nUnsupported LLM provider: {provider}\n")
            return 1
    except Exception as exc:
        print(f"\nFailed to build LLM client: {exc}")
        print("Check LLM_PROVIDER and the matching API key in .env\n")
        return 1

    from extractors.questions_only_pdf_extractor import QuestionsOnlyPDFExtractor
    extractor = QuestionsOnlyPDFExtractor(
        config=config,
        llm_client=llm_client,
        concurrency=args.concurrency,
    )

    print("\n" + "=" * 70)
    print("QUESTIONS-ONLY PDF  ->  MCQ KB GENERATOR")
    print("=" * 70)
    print(f"  PDF:         {pdf_path}")
    print(f"  Output:      {out_path}")
    print(f"  Provider:    {settings.LLM_PROVIDER} / {settings.LLM_MODELS.get(settings.LLM_PROVIDER, '?')}")
    print(f"  Concurrency: {args.concurrency}")
    print()

    try:
        mcqs = await extractor.extract(pdf_path)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except Exception as exc:
        print(f"\nFatal error: {exc}")
        import traceback
        traceback.print_exc()
        return 1

    if not mcqs:
        print("No MCQs generated. Check that the PDF contains bare questions ending with '?'.")
        return 1

    if args.verbose:
        print()
        for i, mcq in enumerate(mcqs, 1):
            line = f"  [{i:03d}] [{mcq.difficulty:6s}] [{mcq.category:13s}] {mcq.question_text[:70]}..."
            print(line.encode("ascii", errors="replace").decode("ascii"))

    # Write to Excel
    rows = [mcq.to_dict() for mcq in mcqs]
    df = pd.DataFrame(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(out_path, index=False)

    print("\n" + "=" * 70)
    print(f"  Generated:   {len(mcqs)} MCQs")
    cat_counts = df["Category"].value_counts().to_dict()
    for cat, cnt in sorted(cat_counts.items()):
        print(f"    {cat}: {cnt}")
    topic_counts = df["Topic"].value_counts().to_dict()
    print(f"  Topics:      {dict(sorted(topic_counts.items()))}")
    diff_counts = df["Difficulty"].value_counts().to_dict()
    print(f"  Difficulty:  {dict(sorted(diff_counts.items()))}")
    print(f"\n  Output KB:   {out_path}")
    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
