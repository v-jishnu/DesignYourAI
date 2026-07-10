"""
Structured File Extractor for MCQ parsing from standard XML and JSON formats.
Allows decoupling layout extraction from database ingestion.
"""

import json
from pathlib import Path
from typing import List, Union, Optional
import xml.etree.ElementTree as ET

from extractors.base_extractor import BaseExtractor
from config.schemas import MCQ


class StructuredFileExtractor(BaseExtractor):
    """Extracts MCQs from pre-formatted XML or JSON files with metadata preservation."""

    async def extract(self, source: Union[str, Path]) -> List[MCQ]:
        """
        Extract MCQs from structured XML or JSON file.

        Args:
            source: Path to the structured file

        Returns:
            List of parsed and validated MCQ objects
        """
        path = Path(source)
        if not path.exists():
            self.log(f"Structured file not found: {path}", 'error')
            return []

        self.log(f"Extracting MCQs from structured file: {path.name}")
        suffix = path.suffix.lower()

        try:
            content = path.read_text(encoding='utf-8')
            
            if suffix == '.json':
                return self._parse_json(content, str(source))
            elif suffix == '.xml':
                return self._parse_xml(content, str(source))
            else:
                self.log(f"Unsupported file format for StructuredFileExtractor: {suffix}", 'error')
                return []
        except Exception as e:
            self.log(f"Error reading structured file {path.name}: {e}", 'error')
            return []

    def _parse_json(self, content: str, source: str) -> List[MCQ]:
        """Parse structured JSON file."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            self.log(f"Malformed JSON: {e}", 'error')
            return []

        if not isinstance(data, list):
            # If it's a single dictionary instead of a list
            data = [data] if isinstance(data, dict) else []

        mcqs = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            
            # Map robust keys
            q_text = self._get_dict_value(item, ['question_text', 'question', 'Question_Text', 'QuestionText'])
            opt_a = self._get_dict_value(item, ['option_a', 'optiona', 'Option_A', 'OptionA'])
            opt_b = self._get_dict_value(item, ['option_b', 'optionb', 'Option_B', 'OptionB'])
            opt_c = self._get_dict_value(item, ['option_c', 'optionc', 'Option_C', 'OptionC'])
            opt_d = self._get_dict_value(item, ['option_d', 'optiond', 'Option_D', 'OptionD'])
            ans = self._get_dict_value(item, ['correct_answer', 'correctanswer', 'Correct_Answer', 'CorrectAnswer', 'answer', 'Answer'])
            exp = self._get_dict_value(item, ['explanation', 'Explanation'])

            mcq = self._create_mcq(
                question_text=q_text,
                option_a=opt_a,
                option_b=opt_b,
                option_c=opt_c,
                option_d=opt_d,
                source=source,
                correct_answer=ans,
                explanation=exp
            )

            if mcq:
                # Add metadata fields
                category = self._get_dict_value(item, ['category', 'Category'])
                topic = self._get_dict_value(item, ['topic', 'Topic'])
                difficulty = self._get_dict_value(item, ['difficulty', 'Difficulty'])
                company = self._get_dict_value(item, ['company', 'Company'])
                job_roles = self._get_dict_value(item, ['job_roles', 'jobroles', 'Job_Roles', 'JobRoles'])

                if category:
                    mcq.category = category
                if topic:
                    mcq.topic = topic
                if difficulty:
                    mcq.difficulty = difficulty
                if company:
                    mcq.company = company
                if job_roles:
                    mcq.job_roles = job_roles

                mcqs.append(mcq)

        self.log(f"Parsed {len(mcqs)} MCQs from JSON file")
        return mcqs

    def _parse_xml(self, content: str, source: str) -> List[MCQ]:
        """Parse structured XML file."""
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            self.log(f"Malformed XML: {e}", 'error')
            return []

        # Support different root node naming (mcqs or root)
        mcq_elements = root.findall('.//mcq')
        if not mcq_elements and root.tag == 'mcq':
            mcq_elements = [root]

        mcqs = []
        for elem in mcq_elements:
            q_text = self._get_xml_value(elem, ['question_text', 'question', 'Question_Text', 'QuestionText'])
            opt_a = self._get_xml_value(elem, ['option_a', 'optiona', 'Option_A', 'OptionA'])
            opt_b = self._get_xml_value(elem, ['option_b', 'optionb', 'Option_B', 'OptionB'])
            opt_c = self._get_xml_value(elem, ['option_c', 'optionc', 'Option_C', 'OptionC'])
            opt_d = self._get_xml_value(elem, ['option_d', 'optiond', 'Option_D', 'OptionD'])
            ans = self._get_xml_value(elem, ['correct_answer', 'correctanswer', 'Correct_Answer', 'CorrectAnswer', 'answer', 'Answer'])
            exp = self._get_xml_value(elem, ['explanation', 'Explanation'])

            mcq = self._create_mcq(
                question_text=q_text,
                option_a=opt_a,
                option_b=opt_b,
                option_c=opt_c,
                option_d=opt_d,
                source=source,
                correct_answer=ans,
                explanation=exp
            )

            if mcq:
                # Add metadata fields
                category = self._get_xml_value(elem, ['category', 'Category'])
                topic = self._get_xml_value(elem, ['topic', 'Topic'])
                difficulty = self._get_xml_value(elem, ['difficulty', 'Difficulty'])
                company = self._get_xml_value(elem, ['company', 'Company'])
                job_roles = self._get_xml_value(elem, ['job_roles', 'jobroles', 'Job_Roles', 'JobRoles'])

                if category:
                    mcq.category = category
                if topic:
                    mcq.topic = topic
                if difficulty:
                    mcq.difficulty = difficulty
                if company:
                    mcq.company = company
                if job_roles:
                    mcq.job_roles = job_roles

                mcqs.append(mcq)

        self.log(f"Parsed {len(mcqs)} MCQs from XML file")
        return mcqs

    def _get_dict_value(self, d: dict, keys: List[str]) -> Optional[str]:
        """Find value in dictionary checking multiple potential key spellings."""
        for key in keys:
            if key in d:
                val = d[key]
                return str(val).strip() if val is not None else None
        return None

    def _get_xml_value(self, parent: ET.Element, tags: List[str]) -> Optional[str]:
        """Find child element value in XML checking multiple potential tag spellings."""
        for tag in tags:
            elem = parent.find(tag)
            if elem is not None:
                # Support nested structures or direct text
                text = elem.text
                return text.strip() if text is not None else ""
        return None
