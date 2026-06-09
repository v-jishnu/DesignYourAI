"""
Post-generation MCQ evaluation and auto-fix CLI.

Reads an Excel knowledge base and independently re-judges every MCQ with an
LLM judge (Ollama locally; any OpenAI-compatible / Gemini API via .env).

Four checks per row:
  1. Answerability   -- are the options well-formed and sufficient?
  2. Blind answer    -- which option does the LLM independently pick?
  3. Answer match    -- does the stored Correct_Answer agree with the blind pick?
  4. Explanation     -- does the explanation justify the marked option?

Modes:

  Evaluate only (default):
    Outputs <kb>_eval.xlsx with Eval_* columns so you can review failures.

  Evaluate + Fix (--fix):
    After evaluation, automatically patches flagged rows:
      WRONG_ANSWER    -> Correct_Answer updated to LLM's blind pick, Explanation rewritten
      BAD_EXPLANATION -> Correct_Answer kept, Explanation rewritten to match it
      NOT_ANSWERABLE  -> row dropped (options are unfixable)
      PASS / INVALID_INPUT / ERROR -> kept unchanged
    Outputs <kb>_final.xlsx -- clean, ready-to-use sheet with no Eval_* columns.

Examples:
    python run_eval.py --excel "C:/path/to/file.xlsx"
    python run_eval.py --excel "C:/path/to/file.xlsx" --fix
    python run_eval.py --excel "C:/path/to/file.xlsx" --fix --verbose
    python run_eval.py --excel "C:/path/to/file.xlsx" --sample 0.1
    python run_eval.py --excel "C:/path/to/file.xlsx" --concurrency 6
"""

import argparse
import asyncio
import sys
from pathlib import Path

from config.settings import settings
from utils.logger import setup_logging


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate and optionally auto-fix an MCQ knowledge base.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Provider is read from LLM_PROVIDER in .env (default: ollama).\n"
            "For local: ensure Ollama is running and qwen2.5:7b is pulled.\n"
            "For API mode: set LLM_PROVIDER=groq (or openai/gemini/deepseek) + key.\n"
        ),
    )

    parser.add_argument(
        "--excel",
        default=None,
        help="Path to the Excel KB to evaluate (default: settings.EXCEL_PATH)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help=(
            "After evaluation, auto-fix flagged rows and write a clean final sheet. "
            "WRONG_ANSWER rows get corrected answers + new explanations. "
            "BAD_EXPLANATION rows get rewritten explanations. "
            "NOT_ANSWERABLE rows are dropped. "
            "Output: <kb>_final.xlsx (no Eval_* columns, ready to use)."
        ),
    )
    parser.add_argument(
        "--sample",
        type=float,
        default=None,
        metavar="FRACTION",
        help="Randomly sample this fraction of rows (e.g. 0.1 = 10%%). Useful for spot-checks.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Judge only the first N rows.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        metavar="N",
        help="Max concurrent LLM calls (default: 2 for Ollama; raise to 6-8 for API providers).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        metavar="DIR",
        help="Directory for output files (default: same directory as the Excel file).",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore any existing resume cache and re-judge all rows from scratch.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-row verdict (and fix status) as rows are processed.",
    )

    return parser.parse_args()


def _print_fix_stats(stats: dict) -> None:
    print("\n" + "=" * 70)
    print("FIX SUMMARY")
    print("=" * 70)
    print(f"  Total rows processed:     {stats['total_rows']}")
    print(f"  Passed (unchanged):       {stats['passed_unchanged']}")
    print(f"  Wrong answers fixed:      {stats['wrong_answer_fixed']}")
    print(f"  Bad explanations fixed:   {stats['bad_explanation_fixed']}")
    print(f"  Not answerable (dropped): {stats['not_answerable_dropped']}")
    print(f"  Invalid input (kept):     {stats['invalid_kept']}")
    print(f"  Error rows (kept):        {stats['error_kept']}")
    print(f"  Fix calls failed (kept):  {stats['fix_failed']}")
    total_fixed = stats['wrong_answer_fixed'] + stats['bad_explanation_fixed']
    print(f"\n  Total rows fixed:         {total_fixed}")
    print(f"  Total rows dropped:       {stats['not_answerable_dropped']}")
    print("=" * 70)


async def _main() -> int:
    args = _parse_args()
    setup_logging(settings.LOG_DIR, settings.LOG_LEVEL)

    # Resolve Excel path
    excel_path = Path(args.excel) if args.excel else settings.EXCEL_PATH
    if not excel_path.exists():
        print(f"\nError: Excel file not found: {excel_path}")
        print("Pass the correct path with --excel\n")
        return 1

    # Resolve output directory
    out_dir = Path(args.output_dir) if args.output_dir else excel_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    eval_xlsx  = out_dir / (excel_path.stem + "_eval.xlsx")
    eval_json  = out_dir / (excel_path.stem + "_eval.json")
    final_xlsx = out_dir / (excel_path.stem + "_final.xlsx")
    cache_path = None if args.no_cache else (out_dir / (excel_path.stem + "_eval_cache.jsonl"))

    # Build config
    try:
        config = settings.get_config()
    except ValueError as exc:
        print(f"\nConfiguration error: {exc}")
        print("Check LLM_PROVIDER and the matching *_API_KEY in your .env file.\n")
        return 1

    mode = "EVALUATE + FIX" if args.fix else "EVALUATE ONLY"
    print("\n" + "=" * 70)
    print(f"MCQ EVALUATION PIPELINE  [{mode}]")
    print("=" * 70)
    print(f"  Excel:    {excel_path}")
    print(f"  Provider: {config['llm_provider']} / {config['llm_model']}")
    print(f"  Sample:   {f'{args.sample*100:.0f}%' if args.sample else 'all rows'}")
    print(f"  Limit:    {args.limit or 'none'}")
    print(f"  Cache:    {'disabled (--no-cache)' if args.no_cache else str(cache_path)}")
    if args.fix:
        print(f"  Final KB: {final_xlsx}")
    print()

    from evaluation.pipeline import EvaluationPipeline
    from evaluation.report import write_all

    pipeline = EvaluationPipeline(
        config=config,
        concurrency=args.concurrency,
        cache_path=cache_path,
    )

    # ---- Step 1: Evaluate ----
    try:
        report = await pipeline.run(
            excel_path=excel_path,
            limit=args.limit,
            sample=args.sample,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        print("\nInterrupted. Partial results saved to cache (re-run to resume).")
        return 130
    except Exception as exc:
        print(f"\nFatal error during evaluation: {exc}")
        import traceback
        traceback.print_exc()
        return 1

    # Always write the eval annotated sheet + JSON
    write_all(report, excel_out=eval_xlsx, json_out=eval_json)

    if not args.fix:
        return 0

    # ---- Step 2: Fix ----
    import pandas as pd
    from evaluation.fixer import MCQFixer
    from evaluation.llm_judge import LLMJudge, build_judge_client

    needs_fix = report.wrong_answer + report.bad_explanation + report.not_answerable
    if needs_fix == 0:
        print("\nNo rows need fixing -- all evaluated rows passed.")
        print(f"Clean sheet written to: {eval_xlsx}  (Eval_* columns present but all PASS)")
        return 0

    print(f"\n{needs_fix} rows flagged for fixing "
          f"({report.wrong_answer} wrong answers, "
          f"{report.bad_explanation} bad explanations, "
          f"{report.not_answerable} not answerable)...")
    print("Running fixer...\n")

    judge_client = build_judge_client(config)
    judge = LLMJudge(judge_client)
    fixer = MCQFixer(judge=judge, concurrency=args.concurrency)

    try:
        df_original = pd.read_excel(excel_path)
        fixed_df, fix_stats = await fixer.fix_dataframe(
            df=df_original,
            report=report,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        print("\nFix step interrupted.")
        return 130
    except Exception as exc:
        print(f"\nFatal error during fix: {exc}")
        import traceback
        traceback.print_exc()
        return 1

    _print_fix_stats(fix_stats)

    # Write final clean sheet -- no Eval_* columns
    eval_cols = [c for c in fixed_df.columns if c.startswith("Eval_")]
    clean_df = fixed_df.drop(columns=eval_cols, errors="ignore")

    try:
        clean_df.to_excel(final_xlsx, index=False)
        print(f"\n  Final clean KB: {final_xlsx}")
        print(f"  ({len(clean_df)} rows, ready to use)\n")
    except Exception as exc:
        print(f"\nFailed to write final sheet: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
