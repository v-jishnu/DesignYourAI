"""Debug PDF extraction to see what text is being extracted."""
import asyncio
from pathlib import Path
from config.settings import Settings
from classifiers.gemini_classifier import GeminiClassifier
from extractors.pdf_extractor import PDFExtractor

async def debug_extraction():
    """Debug PDF extraction."""
    print("=" * 80)
    print("PDF EXTRACTION DEBUG")
    print("=" * 80)

    config = Settings.get_config()
    llm_config = config.get('llm_config', {})
    llm = GeminiClassifier(api_key=llm_config['api_key'], model=llm_config['model'])

    pdf_path = Path(r"c:\Users\V. Jishnu\Downloads\Full_Generative_Models_and_LLM_Content.pdf")

    print(f"\nPDF Path: {pdf_path}")
    print(f"Exists: {pdf_path.exists()}")

    extractor = PDFExtractor(config, llm_client=llm)

    # Extract text
    print("\nExtracting text from PDF...")
    full_text = extractor._extract_text_from_pdf(pdf_path)

    print(f"\nExtracted Text Length: {len(full_text)} characters")
    print("\nFirst 1000 characters:")
    print("-" * 80)
    print(full_text[:1000])
    print("-" * 80)

    # Split into chunks
    print("\nSplitting into chunks...")
    chunks = extractor._split_into_chunks(full_text)
    print(f"Number of chunks: {len(chunks)}")

    # Analyze first 3 chunks
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"\n{'='*80}")
        print(f"CHUNK {i}")
        print(f"{'='*80}")
        print(f"Length: {len(chunk)} chars")
        print(f"Preview (first 200 chars):")
        print(chunk[:200])

        content_type = extractor._detect_content_type(chunk)
        print(f"\nContent Type: {content_type}")

        if content_type == 'qa':
            qa_pairs = extractor._extract_qa_pairs(chunk)
            print(f"Q&A Pairs Found: {len(qa_pairs)}")
            for j, qa in enumerate(qa_pairs[:2], 1):
                print(f"\n  Q&A {j}:")
                print(f"    Q: {qa['question'][:100]}...")
                print(f"    A: {qa['answer'][:100]}...")

    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(debug_extraction())
