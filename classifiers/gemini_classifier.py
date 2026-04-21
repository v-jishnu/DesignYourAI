"""
Google Gemini-based classifier for MCQ categorization (FREE TIER AVAILABLE).
"""

import json
import logging
from typing import List

try:
    from google import genai
except ImportError:
    genai = None

from config.schemas import MCQ
from classifiers.prompt_templates import get_classification_prompt


class GeminiClassifier:
    """
    LLM-based classifier using Google Gemini API.

    FREE TIER: 15 requests per minute, 1500 requests per day
    Model: gemini-1.5-flash (fast and free)
    """

    def __init__(self, api_key: str, model: str = 'gemini-pro'):
        """
        Initialize Gemini classifier.

        Args:
            api_key: Google API key (get from https://makersuite.google.com/app/apikey)
            model: Model identifier (gemini-2.0-flash-exp is free and latest)
        """
        if genai is None:
            raise ImportError(
                "google-genai package required. "
                "Install with: pip install google-genai"
            )

        # Initialize new GenAI client
        self.client = genai.Client(api_key=api_key)
        self.model_name = model
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

        self.logger.info(f"Classifying batch of {len(mcqs)} MCQs with Gemini")

        try:
            # Prepare prompt
            prompt = get_classification_prompt(mcqs, include_examples=False)

            # Call Gemini API with new SDK
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            # Extract response text
            response_text = response.text

            # Parse JSON response
            classifications = self._parse_response(response_text)

            # Apply classifications to MCQs
            for i, classification in enumerate(classifications):
                if i < len(mcqs):
                    mcqs[i].category = classification.get('category')
                    mcqs[i].topic = classification.get('topic')
                    mcqs[i].difficulty = classification.get('difficulty')

            self.logger.info(f"Successfully classified {len(classifications)} MCQs with Gemini")
            return mcqs

        except Exception as e:
            self.logger.error(f"Error classifying batch with Gemini: {e}")
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

            # Remove ```json or ``` markers
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                # Find start and end of JSON
                start_idx = 0
                end_idx = len(lines)

                for i, line in enumerate(lines):
                    if line.strip().startswith('['):
                        start_idx = i
                        break

                for i in range(len(lines)-1, -1, -1):
                    if lines[i].strip().endswith(']'):
                        end_idx = i + 1
                        break

                response_text = '\n'.join(lines[start_idx:end_idx])

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
            self.logger.error(f"Error parsing Gemini response: {e}")
            self.logger.debug(f"Response text: {response_text}")
            return []
