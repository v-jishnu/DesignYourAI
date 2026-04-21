"""Test Q&A to MCQ conversion functionality."""
import asyncio
from pathlib import Path
from config.settings import Settings
from classifiers.gemini_classifier import GeminiClassifier
from extractors.pdf_extractor import PDFExtractor

async def test_qa_patterns():
    """Test Q&A pattern detection."""
    print("=" * 80)
    print("TEST 1: Q&A Pattern Detection")
    print("=" * 80)

    # Test cases with different Q&A formats
    test_cases = [
        """
        Q: What is machine learning?
        A: Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.

        Q: What is supervised learning?
        A: Supervised learning is a type of machine learning where the algorithm learns from labeled training data to make predictions on new, unseen data.
        """,

        """
        1. What is the difference between AI and ML?
        Answer: AI is a broad field encompassing machine learning, while ML is a specific subset of AI focused on learning from data.

        2. What is deep learning?
        Answer: Deep learning is a subset of machine learning that uses neural networks with multiple layers to learn complex patterns from large amounts of data.
        """,

        """
        Question: What is gradient descent?
        Answer: Gradient descent is an optimization algorithm used to minimize the loss function by iteratively moving in the direction of steepest descent.

        Question: What is overfitting?
        Answer: Overfitting occurs when a model learns the training data too well, including noise, resulting in poor performance on new data.
        """
    ]

    config = Settings.get_config()
    extractor = PDFExtractor(config, llm_client=None)

    for i, test_text in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print("-" * 60)

        # Detect content type
        content_type = extractor._detect_content_type(test_text)
        print(f"Content Type: {content_type}")

        # Extract Q&A pairs
        qa_pairs = extractor._extract_qa_pairs(test_text)
        print(f"Q&A Pairs Found: {len(qa_pairs)}")

        for j, qa in enumerate(qa_pairs, 1):
            print(f"\n  Q&A {j}:")
            print(f"    Question: {qa['question'][:80]}...")
            print(f"    Answer: {qa['answer'][:80]}...")

    print("\n" + "=" * 80)
    print("Pattern detection test COMPLETE")
    print("=" * 80)

async def test_qa_conversion():
    """Test Q&A to MCQ conversion with LLM."""
    print("\n" + "=" * 80)
    print("TEST 2: Q&A to MCQ Conversion")
    print("=" * 80)

    config = Settings.get_config()
    llm_config = config.get('llm_config', {})
    llm = GeminiClassifier(api_key=llm_config['api_key'], model=llm_config['model'])

    # Create a test Q&A pair
    test_qa = {
        'question': 'What is the time complexity of binary search?',
        'answer': 'Binary search has a time complexity of O(log n) because it divides the search space in half with each iteration, making it very efficient for searching in sorted arrays.'
    }

    print(f"\nOriginal Q&A:")
    print(f"  Q: {test_qa['question']}")
    print(f"  A: {test_qa['answer']}")

    # Convert to MCQ
    from generators.qa_converter import QAConverter
    converter = QAConverter(llm, config)

    print("\nConverting to MCQ...")
    mcq = await converter.convert_qa_to_mcq(
        question=test_qa['question'],
        answer=test_qa['answer'],
        source='test_qa_conversion.py'
    )

    if mcq:
        print("\nConverted MCQ:")
        print(f"  Question: {mcq.question_text}")
        print(f"  A) {mcq.option_a}")
        print(f"  B) {mcq.option_b}")
        print(f"  C) {mcq.option_c}")
        print(f"  D) {mcq.option_d}")
        print(f"  Correct Answer: {mcq.correct_answer}")
        print(f"  Category: {mcq.category}")
        print("\nConversion SUCCESS")
    else:
        print("\nConversion FAILED")

    print("\n" + "=" * 80)

async def main():
    """Run all tests."""
    try:
        # Test 1: Pattern detection
        await test_qa_patterns()

        # Test 2: Q&A to MCQ conversion with LLM
        await test_qa_conversion()

        print("\nAll tests completed!")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
