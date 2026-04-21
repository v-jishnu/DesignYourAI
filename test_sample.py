"""
Simple test script to verify the MCQ ingestion system works.
This creates a sample MCQ and tests the pipeline without needing real sources.
"""

import asyncio
from config.schemas import MCQ
from config.settings import settings
from agents.classification_agent import ClassificationAgent
from agents.storage_agent import StorageAgent


async def test_system():
    """Test the system with sample MCQs."""

    print("\n" + "="*70)
    print("MCQ INGESTION SYSTEM - SAMPLE TEST")
    print("="*70 + "\n")

    # Create sample MCQs
    sample_mcqs = [
        MCQ(
            question_text="What is the primary purpose of backpropagation in neural networks?",
            option_a="To forward propagate inputs through the network",
            option_b="To calculate gradients and update weights",
            option_c="To initialize network parameters",
            option_d="To evaluate model performance",
            source="test_sample.py",
            correct_answer="B"
        ),
        MCQ(
            question_text="Which algorithm is used for dimensionality reduction?",
            option_a="K-means clustering",
            option_b="Linear Regression",
            option_c="Principal Component Analysis (PCA)",
            option_d="Decision Trees",
            source="test_sample.py",
            correct_answer="C"
        ),
        MCQ(
            question_text="In a distributed system, what is the CAP theorem?",
            option_a="Consistency, Availability, Partition tolerance",
            option_b="Caching, API, Performance",
            option_c="Centralization, Authentication, Privacy",
            option_d="Clustering, Aggregation, Partitioning",
            source="test_sample.py",
            correct_answer="A"
        )
    ]

    print(f"✅ Created {len(sample_mcqs)} sample MCQs\n")

    # Test classification
    try:
        print("🔍 Testing classification...")
        config = settings.get_config()
        classification_agent = ClassificationAgent(config)

        classified_mcqs = await classification_agent.execute(sample_mcqs)

        print("\n📊 Classification Results:")
        for i, mcq in enumerate(classified_mcqs, 1):
            print(f"\n  MCQ {i}:")
            print(f"    Question: {mcq.question_text[:60]}...")
            print(f"    Category: {mcq.category}")
            print(f"    Topic: {mcq.topic}")
            print(f"    Difficulty: {mcq.difficulty}")

    except Exception as e:
        print(f"\n❌ Classification test failed: {e}")
        print("\n💡 Make sure you have set ANTHROPIC_API_KEY in .env file")
        return

    # Test storage
    try:
        print("\n\n💾 Testing storage...")
        storage_agent = StorageAgent(config)

        stored_count = await storage_agent.execute(classified_mcqs)

        print(f"\n✅ Successfully stored {stored_count} MCQs")
        print(f"📁 Knowledge base location: {settings.EXCEL_PATH}")

        # Get total count
        from storage.excel_handler import ExcelHandler
        excel_handler = ExcelHandler(settings.EXCEL_PATH)
        total_count = excel_handler.get_mcq_count()

        print(f"📈 Total MCQs in knowledge base: {total_count}")

    except Exception as e:
        print(f"\n❌ Storage test failed: {e}")
        return

    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("\n🎉 The MCQ ingestion system is working correctly!")
    print("\n📝 Next steps:")
    print("  1. Add your MCQ sources to sources_example.txt")
    print("  2. Run: python main.py --batch sources_example.txt")
    print("  3. Check the Excel file for your ingested MCQs")
    print()


if __name__ == '__main__':
    asyncio.run(test_system())
