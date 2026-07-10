"""
Unit tests for MarkdownTxtExtractor.
Validates plain text/markdown parsing, regex fallback, and ExtractionAgent routing.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest

from extractors.markdown_txt_extractor import MarkdownTxtExtractor
from agents.extraction_agent import ExtractionAgent
from config.schemas import MCQ


@pytest.fixture
def temp_markdown_file(tmp_path):
    """Fixture to create a temporary markdown file with formatted MCQs."""
    md_content = """# Sample AI Interview Questions

1. What is gradient descent?
(a) An optimization algorithm to minimize a cost function.
(b) A classification algorithm for clustering.
(c) A regression algorithm for predictions.
(d) A dimensional reduction technique.

2. In supervised learning, what do labels represent?
(a) Features
(b) Models
(c) Ground truth targets
(d) Gradients

Answers:
1. A
2. C
"""
    file_path = tmp_path / "test_questions.md"
    file_path.write_text(md_content, encoding='utf-8')
    return file_path


@pytest.fixture
def temp_prose_file(tmp_path):
    """Fixture to create a temporary markdown file with only prose content."""
    prose_content = """# Gradient Descent Overview

Gradient descent is an optimization algorithm used to minimize a cost function. 
It iteratively adjusts weights in a neural network to reduce prediction error.
A high learning rate may cause the algorithm to overshoot and oscillate, 
while a low learning rate makes convergence very slow.
"""
    file_path = tmp_path / "test_prose.md"
    file_path.write_text(prose_content, encoding='utf-8')
    return file_path


def test_markdown_txt_extractor_regex_path(temp_markdown_file):
    """Test that MCQs are extracted using the regex fast path from a formatted markdown file."""
    extractor = MarkdownTxtExtractor(config={})
    
    # Mock batch_validate to pass all regex-extracted MCQs
    def mock_batch_validate(mcqs):
        return mcqs, [], {'pass_rate': 1.0}
        
    with patch.object(extractor.validator, 'batch_validate', side_effect=mock_batch_validate):
        mcqs = asyncio.get_event_loop().run_until_complete(extractor.extract(temp_markdown_file))
    
    assert len(mcqs) == 2
    
    assert mcqs[0].question_text == "What is gradient descent?"
    assert mcqs[0].option_a == "An optimization algorithm to minimize a cost function."
    assert mcqs[0].correct_answer == "A"
    
    assert mcqs[1].question_text == "In supervised learning, what do labels represent?"
    assert mcqs[1].option_c == "Ground truth targets"
    assert mcqs[1].correct_answer == "C"


def test_markdown_txt_extractor_llm_fallback(temp_prose_file):
    """Test that prose files trigger the LLM smart fallback."""
    extractor = MarkdownTxtExtractor(config={})
    
    # Mock LLM client and call method
    mock_llm = AsyncMock()
    extractor.llm_client = mock_llm
    
    mock_llm_response = """
    [
      {
        "question_text": "In machine learning model training, how does gradient descent trade-off convergence speed and accuracy when iteratively updating network weights to minimize the loss function?",
        "option_a": "By computing gradients of the cost function with respect to weights and moving in the opposite direction at a speed controlled by the learning rate.",
        "option_b": "By randomly selecting parameters of the cost function and shifting them towards target vectors without taking learning rates into account.",
        "option_c": "By increasing the validation loss monotonically to reach the global minimum and avoid local minimum trade-off points.",
        "option_d": "By performing principal component analysis on the weights to reduce dimensions before applying regular updates in forward pass.",
        "correct_answer": "A",
        "explanation": "Gradient descent adjusts weights by computing gradients and moving in the opposite direction to minimize loss, using the learning rate to control the step size.",
        "category": "Conceptual",
        "topic": "ML",
        "difficulty": "Medium"
      }
    ]
    """
    
    with patch.object(extractor, '_call_llm_with_retry', return_value=mock_llm_response) as mock_retry:
        mcqs = asyncio.get_event_loop().run_until_complete(extractor.extract(temp_prose_file))
        
        assert len(mcqs) == 2
        assert "In machine learning model training" in mcqs[0].question_text
        assert mcqs[0].correct_answer in ["A", "B", "C", "D"]
        mock_retry.assert_called()


def test_extraction_agent_markdown_routing():
    """Verify that .md, .markdown, and .txt files are routed to MarkdownTxtExtractor."""
    config = {
        'llm_config': {
            'provider': 'gemini',
            'api_key': 'mock-key',
            'model': 'gemini-1.5-flash'
        }
    }
    
    agent = ExtractionAgent(config)
    
    md_extractor = agent._get_extractor("notes.md")
    markdown_extractor = agent._get_extractor("notes.markdown")
    txt_extractor = agent._get_extractor("notes.txt")
    
    assert isinstance(md_extractor, MarkdownTxtExtractor)
    assert isinstance(markdown_extractor, MarkdownTxtExtractor)
    assert isinstance(txt_extractor, MarkdownTxtExtractor)
