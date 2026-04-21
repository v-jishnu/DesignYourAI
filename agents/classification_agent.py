"""
Classification agent for categorizing MCQs using LLM.
Supports multiple providers: Gemini, Claude, OpenAI, Groq, Together.ai
"""

from typing import List

from agents.base_agent import BaseAgent
from config.schemas import MCQ


class ClassificationAgent(BaseAgent):
    """Classifies MCQs using LLM (multi-provider support)."""

    def __init__(self, config: dict):
        """Initialize classification agent."""
        super().__init__("ClassificationAgent", config)

        # Select classifier based on provider
        provider = config.get('llm_provider', 'gemini')
        api_key = config['llm_api_key']
        model = config.get('llm_model', 'gemini-1.5-flash')
        base_url = config.get('llm_base_url')

        self.log_action(f"Using LLM provider: {provider} (model: {model})")

        if provider == 'gemini':
            from classifiers.gemini_classifier import GeminiClassifier
            self.llm_classifier = GeminiClassifier(api_key=api_key, model=model)

        elif provider == 'anthropic':
            from classifiers.llm_classifier import LLMClassifier
            self.llm_classifier = LLMClassifier(api_key=api_key, model=model)

        elif provider in ['openai', 'groq', 'together', 'qwen', 'deepseek', 'ollama']:
            from classifiers.openai_classifier import OpenAIClassifier
            self.llm_classifier = OpenAIClassifier(
                api_key=api_key,
                model=model,
                base_url=base_url
            )

        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        self.batch_size = config.get('classification_batch_size', 10)

    async def execute(self, mcqs: List[MCQ]) -> List[MCQ]:
        """
        Classify all MCQs in batches.

        Args:
            mcqs: List of MCQs to classify

        Returns:
            Same list with classifications added
        """
        if not mcqs:
            return mcqs

        self.log_action(f"Classifying {len(mcqs)} MCQs in batches of {self.batch_size}")

        classified_mcqs = []

        for i in range(0, len(mcqs), self.batch_size):
            batch = mcqs[i:i+self.batch_size]
            batch_num = (i // self.batch_size) + 1

            try:
                classified_batch = await self.llm_classifier.classify_batch(batch)
                classified_mcqs.extend(classified_batch)
                self.log_action(f"Classified batch {batch_num} ({len(classified_batch)} MCQs)")

            except Exception as e:
                self.handle_error(e, f"classification batch {batch_num}")
                # Add unclassified MCQs
                classified_mcqs.extend(batch)

        self.log_action(f"Classification complete: {len(classified_mcqs)} MCQs")
        return classified_mcqs
