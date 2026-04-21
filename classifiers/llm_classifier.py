"""
LLM-based classifier for MCQ categorization using Claude.
"""

import json
import logging
from typing import List

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from config.schemas import MCQ
from classifiers.prompt_templates import get_classification_prompt


class LLMClassifier:
    """LLM-based classifier using Claude API."""

    def __init__(self, api_key: str, model: str = 'claude-3-5-sonnet-20241022'):
        """
        Initialize LLM classifier.

        Args:
            api_key: Anthropic API key
            model: Model identifier
        """
        if Anthropic is None:
            raise ImportError("anthropic package required. Install with: pip install anthropic")

        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.logger = logging.getLogger(__name__)

    async def classify_batch(self, mcqs: List[MCQ]) -> List[MCQ]:
        """
        Classify a batch of MCQs.

        Args:
            mcqs: List of MCQs to classify

        Returns:
            Same list with category, topic, difficulty filled in
        """
        if not mcqs:
            return mcqs

        self.logger.info(f"Classifying batch of {len(mcqs)} MCQs")

        try:
            # Prepare prompt
            prompt = get_classification_prompt(mcqs, include_examples=False)

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract response text
            response_text = response.content[0].text

            # Parse JSON response
            classifications = self._parse_response(response_text)

            # Apply classifications to MCQs
            for i, classification in enumerate(classifications):
                if i < len(mcqs):
                    mcqs[i].category = classification.get('category')
                    mcqs[i].topic = classification.get('topic')
                    mcqs[i].difficulty = classification.get('difficulty')

            self.logger.info(f"Successfully classified {len(classifications)} MCQs")
            return mcqs

        except Exception as e:
            self.logger.error(f"Error classifying batch: {e}")
            # Return MCQs without classification rather than failing
            return mcqs

    def _parse_response(self, response_text: str) -> List[dict]:
        """
        Parse LLM response into structured classifications.

        Args:
            response_text: Response from LLM

        Returns:
            List of classification dictionaries
        """
        try:
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]

            response_text = response_text.strip()

            # Parse JSON
            classifications = json.loads(response_text)

            # Validate structure
            if not isinstance(classifications, list):
                raise ValueError("Response is not a list")

            # Ensure all required fields
            valid_classifications = []
            for item in classifications:
                if all(key in item for key in ['category', 'topic', 'difficulty']):
                    valid_classifications.append(item)

            return valid_classifications

        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {e}")
            return []
