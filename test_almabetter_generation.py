"""Test content generation on AlmaBetter page."""
import asyncio
from extractors.web_extractor import WebExtractor
from config.settings import Settings
from classifiers.gemini_classifier import GeminiClassifier

async def test():
    config = Settings.get_config()
    llm_config = config.get('llm_config', {})
    llm = GeminiClassifier(api_key=llm_config['api_key'], model=llm_config['model'])

    extractor = WebExtractor(config, llm_client=llm)

    print("Generating MCQs from AlmaBetter content...")
    mcqs = await extractor._generate_from_page_content(
        'https://www.almabetter.com/bytes/articles/top-maang-interview-questions-ai-roles'
    )

    print(f"\nGenerated {len(mcqs)} MCQs\n")

    for i, mcq in enumerate(mcqs, 1):
        print(f"{i}. {mcq.question_text}")
        print(f"   A) {mcq.option_a[:60]}...")
        print(f"   B) {mcq.option_b[:60]}...")
        print(f"   C) {mcq.option_c[:60]}...")
        print(f"   D) {mcq.option_d[:60]}...")
        print(f"   Correct: {mcq.correct_answer}")
        print(f"   Category: {mcq.category}\n")

asyncio.run(test())
