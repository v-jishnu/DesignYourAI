"""
Drop-in ingestion CLI.

Single front door for the MCQ generation engine. Accepts a public URL, a local
PDF, a local file, or a batch file, and routes through the existing
IngestionAgent (extraction -> classification -> dedup -> storage).

This wrapper does NOT duplicate pipeline logic — it only:
  1. Normalizes CLI flags into a list of sources.
  2. Optionally previews shape detection via --dry-run (no LLM, no writes).
  3. Calls IngestionAgent.execute(sources) and prints a clean progress block.
  4. Applies --limit and --output as per-run config overrides.

Login-gated content is NOT supported. For gated pages, export the page to PDF
first and pass it via --pdf.

Examples:
    python run_ingest.py --url https://github.com/kojino/120-Data-Science-Interview-Questions
    python run_ingest.py --url https://github.com/kojino/120-Data-Science-Interview-Questions --dry-run
    python run_ingest.py --pdf data/raw/interview-prep.pdf --limit 20
    python run_ingest.py --file notes.md
    python run_ingest.py --batch sources.txt
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List

from config.settings import settings
from utils.logger import setup_logging


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Drop-in MCQ ingestion: feed a URL, PDF, or file and get quality MCQs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Notes:\n"
            "  - Only PUBLIC URLs are supported. For login-gated content, export to PDF first.\n"
            "  - Output lands in the existing Excel KB at settings.EXCEL_PATH (unless --output).\n"
            "  - --dry-run fetches + detects shape but does NOT call the LLM or write to Excel.\n"
        ),
    )

    src = parser.add_mutually_exclusive_group()
    src.add_argument("--url", help="Public URL to ingest (any site, or a GitHub repo)")
    src.add_argument("--pdf", help="Path to a local PDF file")
    src.add_argument("--file", help="Path to a local .md / .txt / .docx file")
    src.add_argument("--batch", help="Path to a text file with one source per line")

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap MCQs processed per source (passed to extractors)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch + detect shape only; no LLM calls, no Excel writes",
    )
    parser.add_argument(
        "--output",
        help="Override output Excel path (defaults to settings.EXCEL_PATH)",
    )

    return parser.parse_args()


def _collect_sources(args: argparse.Namespace) -> List[str]:
    if args.url:
        return [args.url]
    if args.pdf:
        return [args.pdf]
    if args.file:
        return [args.file]
    if args.batch:
        batch_path = Path(args.batch)
        if not batch_path.exists():
            print(f"Batch file not found: {args.batch}")
            sys.exit(1)
        lines = batch_path.read_text(encoding="utf-8").splitlines()
        return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    return []


async def _dry_run(sources: List[str]) -> None:
    """Fetch + shape-detect each source without calling the LLM or writing."""
    from ingestion.shape_detector import detect_shape

    print("\n" + "=" * 70)
    print("DRY RUN - shape detection only (no LLM, no writes)")
    print("=" * 70)

    for i, source in enumerate(sources, 1):
        print(f"\n[{i}/{len(sources)}] {source}")
        try:
            text = await _fetch_text_for_preview(source)
        except Exception as e:
            print(f"  [fail] fetch failed: {e}")
            continue

        if not text:
            print("  [fail] no text extracted")
            continue

        report = detect_shape(text)
        print(f"  [ok] fetched {report.word_count} words")
        print(f"  -> shape: {report.shape.upper()}  ({report.note})")


async def _fetch_text_for_preview(source: str) -> str:
    """Lightweight fetch for --dry-run preview. Handles URLs, PDFs, local files."""
    source_str = str(source).lower()
    path = Path(source)

    # Local files first
    if path.exists() and path.is_file():
        if source_str.endswith(".pdf"):
            try:
                import pdfplumber
            except ImportError:
                raise RuntimeError("pdfplumber not installed")
            text_parts = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text_parts.append(page.extract_text() or "")
            return "\n".join(text_parts)
        return path.read_text(encoding="utf-8", errors="ignore")

    # PDF URL
    if source_str.startswith("http") and source_str.endswith(".pdf"):
        import tempfile
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(source, timeout=30) as resp:
                resp.raise_for_status()
                data = await resp.read()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    text_parts.append(page.extract_text() or "")
            return "\n".join(text_parts)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    # GitHub URLs -> fetch raw markdown text of first file we find
    if "github.com" in source_str or "raw.githubusercontent.com" in source_str:
        # Delegate to the GitHub extractor's resolver/fetcher for accuracy
        from extractors.github_markdown_extractor import GitHubMarkdownExtractor
        config = settings.get_config()
        ext = GitHubMarkdownExtractor(config)
        try:
            raw_urls = await ext._resolve_to_raw_urls(source)
            if not raw_urls:
                return ""
            # Combine up to 3 files for a representative shape sample
            texts = []
            for url in raw_urls[:3]:
                try:
                    texts.append(await ext._fetch_raw(url))
                except Exception:
                    continue
            return "\n\n".join(texts)
        finally:
            await ext._close_session()

    # Generic URL -> static HTML fetch + strip tags
    if source_str.startswith("http"):
        import aiohttp
        from bs4 import BeautifulSoup

        async with aiohttp.ClientSession() as session:
            async with session.get(source, timeout=30) as resp:
                html = await resp.text()
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text()

    raise ValueError(f"Unsupported source: {source}")


def _apply_overrides(config: dict, args: argparse.Namespace) -> dict:
    if args.limit is not None:
        # Downstream extractors look for these keys
        config["generation_num_questions"] = min(args.limit, 50)
        config["github_max_conversions_per_file"] = args.limit
        config["stratascratch_max_details"] = args.limit
    if args.output:
        config["excel_path"] = Path(args.output)
    return config


def _print_header(sources: List[str], dry_run: bool, output_path: Path) -> None:
    print("\n" + "=" * 70)
    print("MCQ INGESTION - DROP-IN MODE")
    print("=" * 70)
    print(f"  Sources: {len(sources)}")
    for i, s in enumerate(sources, 1):
        print(f"    {i}. {s}")
    print(f"  Provider: {settings.LLM_PROVIDER}")
    print(f"  Model: {settings.LLM_MODELS.get(settings.LLM_PROVIDER)}")
    print(f"  Output: {output_path}")
    if dry_run:
        print("  Mode: DRY RUN (no LLM, no writes)")
    print()


def _print_results(results: dict, output_path: Path) -> None:
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"  Extracted:  {results.get('total_extracted', 0)}")
    print(f"  Classified: {results.get('total_classified', 0)}")
    print(f"  Duplicates: {results.get('duplicates_found', 0)}")
    print(f"  Stored:     {results.get('total_stored', 0)}")

    dist = results.get("distribution") or {}
    total = sum(dist.values())
    if total:
        print("\n  Category distribution:")
        for cat in ("Conceptual", "Mathematical", "Application"):
            n = dist.get(cat, 0)
            pct = n / total * 100 if total else 0
            print(f"    - {cat}: {n} ({pct:.1f}%)")

    errors = results.get("errors") or []
    if errors:
        print("\n  Errors:")
        for err in errors:
            print(f"    - {err}")

    print(f"\nOutput: {output_path}")
    print("=" * 70 + "\n")


async def _main() -> int:
    args = _parse_args()
    setup_logging(settings.LOG_DIR, settings.LOG_LEVEL)

    try:
        settings.validate()
    except ValueError as e:
        print(f"\nConfiguration error: {e}")
        print("Create a .env file with your provider's API key (see .env.template)\n")
        return 1

    sources = _collect_sources(args)
    if not sources:
        print("No source provided. Use one of: --url, --pdf, --file, --batch")
        return 1

    config = settings.get_config()
    config = _apply_overrides(config, args)
    output_path = Path(config.get("excel_path", settings.EXCEL_PATH))

    _print_header(sources, args.dry_run, output_path)

    if args.dry_run:
        await _dry_run(sources)
        return 0

    # Lazy import so --dry-run and --help don't pay the agent init cost
    from agents.ingestion_agent import IngestionAgent

    agent = IngestionAgent(config)
    try:
        results = await agent.execute(sources)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        return 130
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    _print_results(results, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
