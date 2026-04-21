"""
OpenAI GPT-based classifier for MCQ categorization.
Can be used with OpenAI-compatible APIs (like together.ai, groq, etc.)
"""

import json
import logging
from typing import List

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from config.schemas import MCQ
from classifiers.prompt_templates import get_classification_prompt


class OpenAIClassifier:
    """
    LLM-based classifier using OpenAI API or compatible services.

    Compatible with:
    - OpenAI GPT-4, GPT-3.5
    - Together.ai (free tier available)
    - Groq (free tier available)
    - Any OpenAI-compatible API
    """

    def __init__(
        self,
        api_key: str,
        model: str = 'gpt-3.5-turbo',
        base_url: str = None
    ):
        """
        Initialize OpenAI-compatible classifier.

        Args:
            api_key: API key
            model: Model identifier
            base_url: Optional base URL for compatible APIs
                     (e.g., "https://api.together.xyz/v1")
        """
        if OpenAI is None:
            raise ImportError(
                "openai package required. "
                "Install with: pip install openai"
            )

        try:
            if base_url:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)
        except TypeError as e:
            if 'proxies' in str(e):
                # Fallback for older OpenAI versions
                import os
                os.environ['OPENAI_API_KEY'] = api_key
                if base_url:
                    os.environ['OPENAI_BASE_URL'] = base_url
                self.client = OpenAI(api_key=api_key)
            else:
                raise

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

        self.logger.info(f"Classifying batch of {len(mcqs)} MCQs with OpenAI-compatible API")

        try:
            # Prepare prompt
            prompt = get_classification_prompt(mcqs, include_examples=False)

            # Call API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            # Extract response text
            response_text = response.choices[0].message.content

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
        """Parse LLM response into structured classifications."""
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
            self.logger.error(f"Error parsing response: {e}")
            return []
