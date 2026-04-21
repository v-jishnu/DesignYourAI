"""
Data models and schemas for MCQ ingestion system.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime
import uuid


@dataclass
class MCQ:
    """Standard MCQ data structure."""

    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    source: str

    # Optional fields
    question_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correct_answer: Optional[Literal['A', 'B', 'C', 'D']] = None
    explanation: Optional[str] = None
    category: Optional[Literal['Conceptual', 'Mathematical', 'Application']] = None
    topic: Optional[Literal['AI', 'ML', 'Data Science', 'System Design']] = None
    difficulty: Optional[Literal['Easy', 'Medium', 'Hard']] = None
    date_added: datetime = field(default_factory=datetime.now)
    used_status: bool = False

    # For deduplication
    hash_value: Optional[str] = None

    # Metadata fields (optional, from platform-specific extractors)
    company: Optional[str] = None
    job_roles: Optional[str] = None

    # Image fields (for visual MCQs)
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    image_filename: Optional[str] = None
    has_image: bool = False
    image_format: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert MCQ to dictionary for Excel storage."""
        return {
            'Question_ID': self.question_id,
            'Question_Text': self.question_text,
            'Option_A': self.option_a,
            'Option_B': self.option_b,
            'Option_C': self.option_c,
            'Option_D': self.option_d,
            'Correct_Answer': self.correct_answer,
            'Explanation': self.explanation,
            'Category': self.category,
            'Topic': self.topic,
            'Difficulty': self.difficulty,
            'Source': self.source,
            'Date_Added': self.date_added.strftime('%Y-%m-%d %H:%M:%S'),
            'Used_Status': self.used_status,
            'Company': self.company,
            'Job_Roles': self.job_roles,
            'Image_Path': self.image_path,
            'Image_URL': self.image_url,
            'Has_Image': self.has_image,
            'Image_Format': self.image_format
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MCQ':
        """Create MCQ from dictionary (Excel row)."""
        return cls(
            question_id=data.get('Question_ID', str(uuid.uuid4())),
            question_text=data['Question_Text'],
            option_a=data['Option_A'],
            option_b=data['Option_B'],
            option_c=data['Option_C'],
            option_d=data['Option_D'],
            correct_answer=data.get('Correct_Answer'),
            explanation=data.get('Explanation'),
            category=data.get('Category'),
            topic=data.get('Topic'),
            difficulty=data.get('Difficulty'),
            source=data.get('Source', ''),
            date_added=cls._parse_date(data.get('Date_Added', datetime.now())),
            used_status=bool(data.get('Used_Status', False)),
            company=data.get('Company'),
            job_roles=data.get('Job_Roles'),
            image_path=data.get('Image_Path'),
            image_url=data.get('Image_URL'),
            image_filename=data.get('Image_Path').split('/')[-1] if data.get('Image_Path') and isinstance(data.get('Image_Path'), str) else None,
            has_image=bool(data.get('Has_Image', False)),
            image_format=data.get('Image_Format')
        )

    @staticmethod
    def _parse_date(date_value):
        """
        Parse date from various formats (string, float, datetime).

        Handles:
        - String format: '2024-01-15 10:30:00'
        - Excel serial date (float): 45321.5
        - datetime object: datetime(2024, 1, 15, 10, 30, 0)
        - None/NaN: returns current datetime
        """
        import pandas as pd

        # None or NaN
        if date_value is None or (isinstance(date_value, float) and pd.isna(date_value)):
            return datetime.now()

        # Already datetime object
        if isinstance(date_value, datetime):
            return date_value

        # Excel serial date (float)
        if isinstance(date_value, (int, float)):
            try:
                # Excel epoch starts at 1900-01-01
                # pandas.to_datetime handles Excel serial dates
                return pd.to_datetime(date_value, unit='D', origin='1899-12-30')
            except:
                return datetime.now()

        # String format
        if isinstance(date_value, str):
            try:
                return datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S')
            except:
                try:
                    # Try alternative format
                    return datetime.strptime(date_value, '%Y-%m-%d')
                except:
                    return datetime.now()

        # Fallback
        return datetime.now()

    def is_valid(self) -> bool:
        """Check if MCQ has all required fields."""
        return bool(
            self.question_text and
            self.option_a and
            self.option_b and
            self.option_c and
            self.option_d and
            self.source
        )

    def __repr__(self) -> str:
        """String representation of MCQ."""
        return f"MCQ(id={self.question_id[:8]}..., category={self.category}, topic={self.topic})"
