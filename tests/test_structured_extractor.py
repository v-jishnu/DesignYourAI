"""
Unit tests for StructuredFileExtractor.
Validates XML/JSON parsing, robustness with respect to tags, and ExtractionAgent routing.
"""

import json
import asyncio
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest

from extractors.structured_file_extractor import StructuredFileExtractor
from agents.extraction_agent import ExtractionAgent
from config.schemas import MCQ


@pytest.fixture
def temp_files(tmp_path):
    """Fixture to create temporary XML and JSON files."""
    json_data = [
        {
            "question_text": "What is overfitting?",
            "option_a": "High bias, low variance",
            "option_b": "Low bias, high variance",
            "option_c": "Low bias, low variance",
            "option_d": "High bias, high variance",
            "correct_answer": "B",
            "explanation": "Overfitting happens when a model learns noise in training data, leading to low training error but high test error.",
            "category": "Conceptual",
            "topic": "ML",
            "difficulty": "Medium",
            "company": "Google",
            "job_roles": "MLE"
        }
    ]

    xml_data = """<?xml version="1.0" encoding="utf-8"?>
<mcqs>
  <mcq>
    <question_text>What is underfitting?</question_text>
    <option_a>High bias, low variance</option_a>
    <option_b>Low bias, high variance</option_b>
    <option_c>Low bias, low variance</option_c>
    <option_d>High bias, high variance</option_d>
    <correct_answer>A</correct_answer>
    <explanation>Underfitting happens when the model is too simple to capture patterns.</explanation>
    <category>Conceptual</category>
    <topic>ML</topic>
    <difficulty>Easy</difficulty>
    <company>Meta</company>
    <job_roles>Research Scientist</job_roles>
  </mcq>
</mcqs>
"""

    json_file = tmp_path / "test.json"
    xml_file = tmp_path / "test.xml"

    json_file.write_text(json.dumps(json_data), encoding='utf-8')
    xml_file.write_text(xml_data, encoding='utf-8')

    return json_file, xml_file


def test_json_parsing(temp_files):
    json_file, _ = temp_files
    extractor = StructuredFileExtractor(config={})
    
    mcqs = asyncio.get_event_loop().run_until_complete(extractor.extract(json_file))
    assert len(mcqs) == 1
    mcq = mcqs[0]
    assert mcq.question_text == "What is overfitting?"
    assert mcq.option_a == "High bias, low variance"
    assert mcq.option_b == "Low bias, high variance"
    assert mcq.correct_answer == "B"
    assert mcq.explanation == "Overfitting happens when a model learns noise in training data, leading to low training error but high test error."
    assert mcq.category == "Conceptual"
    assert mcq.topic == "ML"
    assert mcq.difficulty == "Medium"
    assert mcq.company == "Google"
    assert mcq.job_roles == "MLE"


def test_xml_parsing(temp_files):
    _, xml_file = temp_files
    extractor = StructuredFileExtractor(config={})
    
    mcqs = asyncio.get_event_loop().run_until_complete(extractor.extract(xml_file))
    assert len(mcqs) == 1
    mcq = mcqs[0]
    assert mcq.question_text == "What is underfitting?"
    assert mcq.option_a == "High bias, low variance"
    assert mcq.option_b == "Low bias, high variance"
    assert mcq.correct_answer == "A"
    assert mcq.explanation == "Underfitting happens when the model is too simple to capture patterns."
    assert mcq.category == "Conceptual"
    assert mcq.topic == "ML"
    assert mcq.difficulty == "Easy"
    assert mcq.company == "Meta"
    assert mcq.job_roles == "Research Scientist"


def test_extraction_agent_routing():
    config = {
        'llm_provider': 'gemini',
        'llm_api_key': 'mock-key',
        'llm_model': 'gemini-1.5-flash',
        'excel_path': 'dummy.xlsx',
        'llm_config': {
            'provider': 'gemini',
            'api_key': 'mock-key',
            'model': 'gemini-1.5-flash'
        }
    }
    
    agent = ExtractionAgent(config)
    
    json_extractor = agent._get_extractor("test.json")
    xml_extractor = agent._get_extractor("test.xml")
    
    assert isinstance(json_extractor, StructuredFileExtractor)
    assert isinstance(xml_extractor, StructuredFileExtractor)
