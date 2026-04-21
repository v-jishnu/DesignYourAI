"""Test mixed content extraction (MCQs + Q&A) from text file."""
import asyncio
import pandas as pd
from pathlib import Path
from config.settings import Settings
from agents.extraction_agent import ExtractionAgent
from agents.classification_agent import ClassificationAgent
from storage.excel_handler import ExcelHandler

async def test_mixed_content_extraction():
    """Test extraction and conversion from mixed content file."""
    print("=" * 80)
    print("MIXED CONTENT EXTRACTION TEST")
    print("=" * 80)

    # Initialize config and agents
    config = Settings.get_config()
    extraction_agent = ExtractionAgent(config)
    classification_agent = ClassificationAgent(config)
    excel_path = config.get('storage', {}).get('excel_path', 'data/knowledge_base/mcq_knowledge_base.xlsx')
    excel_handler = ExcelHandler(excel_path)

    # Prepare test file
    test_file = Path("test_files/sample_mixed_content.txt")

    # Create a simple text-to-PDF converter or just copy as .txt
    # For simplicity, we'll manually create structured content
    print(f"\nTest file: {test_file}")
    print(f"File exists: {test_file.exists()}")

    if not test_file.exists():
        print("ERROR: Test file not found!")
        return

    # Read content
    content = test_file.read_text()
    print(f"\nContent preview (first 300 chars):")
    print(content[:300])
    print("...")

    # Simulate extraction (since we have .txt not .pdf)
    # We'll test the pattern detection manually
    from extractors.pdf_extractor import PDFExtractor
    from classifiers.gemini_classifier import GeminiClassifier

    llm_config = config.get('llm_config', {})
    llm = GeminiClassifier(api_key=llm_config['api_key'], model=llm_config['model'])

    extractor = PDFExtractor(config, llm_client=llm)

    print("\n" + "-" * 80)
    print("STEP 1: Content Type Detection")
    print("-" * 80)

    # Split content into chunks
    chunks = extractor._split_into_chunks(content)
    print(f"\nFound {len(chunks)} chunks")

    mcqs = []
    qa_pairs = []

    for i, chunk in enumerate(chunks, 1):
        content_type = extractor._detect_content_type(chunk)
        print(f"\nChunk {i} ({len(chunk)} chars): {content_type}")
        print(f"  Preview: {chunk[:80]}...")

        if content_type == 'mcq':
            # Try to extract MCQs
            chunk_mcqs = extractor._parse_mcq_text(chunk, str(test_file))
            if chunk_mcqs:
                print(f"  -> Extracted {len(chunk_mcqs)} MCQ(s)")
                mcqs.extend(chunk_mcqs)

        elif content_type == 'qa':
            # Extract Q&A pairs
            chunk_qas = extractor._extract_qa_pairs(chunk)
            if chunk_qas:
                print(f"  -> Found {len(chunk_qas)} Q&A pair(s)")
                qa_pairs.extend(chunk_qas)

    print("\n" + "-" * 80)
    print("STEP 2: Q&A to MCQ Conversion")
    print("-" * 80)

    if qa_pairs:
        print(f"\nConverting {len(qa_pairs)} Q&A pairs to MCQs...")
        converted_mcqs = await extractor._convert_qa_pairs(qa_pairs, str(test_file))
        print(f"Successfully converted {len(converted_mcqs)} Q&A pairs")
        mcqs.extend(converted_mcqs)
    else:
        print("\nNo Q&A pairs to convert")

    print("\n" + "-" * 80)
    print("STEP 3: Category Classification")
    print("-" * 80)

    if mcqs:
        print(f"\nClassifying {len(mcqs)} MCQs...")
        classified_mcqs = await classification_agent.execute(mcqs)
        print(f"Classified {len(classified_mcqs)} MCQs")

        # Show results
        print("\n" + "=" * 80)
        print("EXTRACTED & CLASSIFIED MCQs")
        print("=" * 80)

        for i, mcq in enumerate(classified_mcqs, 1):
            print(f"\n{i}. {mcq.question_text}")
            print(f"   A) {mcq.option_a[:60]}...")
            print(f"   B) {mcq.option_b[:60]}...")
            print(f"   C) {mcq.option_c[:60]}...")
            print(f"   D) {mcq.option_d[:60]}...")
            print(f"   Correct: {mcq.correct_answer}")
            print(f"   Category: {mcq.category}")
            print(f"   Topic: {mcq.topic}")
            print(f"   Difficulty: {mcq.difficulty}")

        # Save to Excel
        print("\n" + "-" * 80)
        print("STEP 4: Save to Excel")
        print("-" * 80)

        print("\nSaving to Excel...")
        saved_count = excel_handler.append_mcqs(classified_mcqs)
        print(f"Saved {saved_count} MCQs to Excel!")

        # Verify in Excel
        print("\n" + "-" * 80)
        print("VERIFICATION")
        print("-" * 80)

        df = pd.read_excel('data/knowledge_base/mcq_knowledge_base.xlsx')
        print(f"\nTotal MCQs in Excel: {len(df)}")

        # Get last N MCQs (the ones we just added)
        recent = df.tail(len(classified_mcqs))
        print(f"\nLast {len(classified_mcqs)} MCQs:")

        # Check categories
        print("\nCategory Distribution:")
        print(recent['Category'].value_counts())

        # Verify no null categories
        null_categories = recent['Category'].isnull().sum()
        if null_categories > 0:
            print(f"\nWARNING: {null_categories} MCQs missing categories!")
        else:
            print("\nSUCCESS: All MCQs have categories assigned!")

    else:
        print("\nNo MCQs extracted - check patterns and content format")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_mixed_content_extraction())
