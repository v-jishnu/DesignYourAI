"""
Extraction agent for coordinating MCQ extraction from sources.
"""

from typing import List, Union
from pathlib import Path

from agents.base_agent import BaseAgent
from config.schemas import MCQ
from extractors.web_extractor import WebExtractor
from extractors.pdf_extractor import PDFExtractor
from extractors.docx_extractor import DOCXExtractor
from extractors.stratascratch_extractor import StrataScratchExtractor
from extractors.github_markdown_extractor import GitHubMarkdownExtractor


class ExtractionAgent(BaseAgent):
    """Manages extraction from multiple source types."""

    def __init__(self, config: dict):
        """Initialize extraction agent."""
        super().__init__("ExtractionAgent", config)

        # Initialize LLM client for content generation based on provider
        llm_config = self.config.get('llm_config', {})
        provider = llm_config.get('provider', 'gemini')

        if provider == 'gemini':
            from classifiers.gemini_classifier import GeminiClassifier
            self.llm_client = GeminiClassifier(
                api_key=llm_config['api_key'],
                model=llm_config['model']
            )
        elif provider in ['groq', 'openai', 'together', 'qwen', 'deepseek', 'ollama']:
            # Use OpenAI-compatible client for Groq/OpenAI/Together/Qwen/DeepSeek/Ollama
            from openai import AsyncOpenAI
            base_url = self.config.get('llm_base_url')
            self.llm_client = AsyncOpenAI(
                api_key=llm_config['api_key'],
                base_url=base_url
            )
            self.llm_client.model_name = llm_config['model']
            self.llm_client.provider = provider
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        # Pass llm_client to extractors for content generation fallback
        self.extractors = {
            'web': WebExtractor(config, llm_client=self.llm_client),
            'pdf': PDFExtractor(config, llm_client=self.llm_client),
            'docx': DOCXExtractor(config, llm_client=self.llm_client),
            'stratascratch': StrataScratchExtractor(config, llm_client=self.llm_client),
            'github': GitHubMarkdownExtractor(config, llm_client=self.llm_client),
        }

    async def execute(self, sources: List[Union[str, Path]]) -> List[MCQ]:
        """
        Extract MCQs from all sources.

        Args:
            sources: List of URLs or file paths

        Returns:
            List of extracted MCQs from all sources
        """
        all_mcqs = []

        for source in sources:
            try:
                extractor = self._get_extractor(source)
                mcqs = await extractor.extract(source)
                all_mcqs.extend(mcqs)
                self.log_action(f"Extracted {len(mcqs)} MCQs from {source}")

            except Exception as e:
                self.handle_error(e, f"extraction from {source}")
                # Continue with next source

        self.log_action(f"Total extracted: {len(all_mcqs)} MCQs from {len(sources)} sources")
        return all_mcqs

    def _get_extractor(self, source: Union[str, Path]):
        """Determine which extractor to use."""
        source_str = str(source).lower()

        # Check for platform-specific extractors first
        if 'stratascratch' in source_str:
            return self.extractors['stratascratch']

        # GitHub repos / raw markdown get the dedicated Q&A-aware extractor
        if 'github.com' in source_str or 'raw.githubusercontent.com' in source_str:
            return self.extractors['github']

        # Check file extension (handles both URLs and local files)
        if source_str.endswith('.pdf'):
            return self.extractors['pdf']
        elif source_str.endswith('.docx'):
            return self.extractors['docx']
        elif source_str.startswith('http'):
            # Web extractor for HTML pages
            return self.extractors['web']
        else:
            raise ValueError(f"Unsupported source type: {source}")
