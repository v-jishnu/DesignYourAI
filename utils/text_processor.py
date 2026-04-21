"""
Text processing utilities for normalization and cleaning.
"""

import re
from typing import Optional


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison and deduplication.

    Args:
        text: Input text to normalize

    Returns:
        Normalized text

    Processing steps:
    - Convert to lowercase
    - Remove extra whitespace
    - Remove punctuation
    - Strip leading/trailing whitespace
    """
    # Convert to lowercase
    text = text.lower()

    # Remove extra whitespace (multiple spaces/newlines to single space)
    text = re.sub(r'\s+', ' ', text)

    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)

    # Strip whitespace
    return text.strip()


def clean_text(text: str) -> str:
    """
    Clean text while preserving structure.

    Args:
        text: Input text to clean

    Returns:
        Cleaned text

    Processing steps:
    - Remove excessive whitespace
    - Normalize line endings
    - Strip HTML tags if present
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Remove excessive newlines (more than 2)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove excessive spaces
    text = re.sub(r' {2,}', ' ', text)

    # Strip
    return text.strip()


def extract_option_text(text: str) -> str:
    """
    Extract option text from formatted strings.

    Args:
        text: Option text possibly with prefix like "A)", "a.", etc.

    Returns:
        Clean option text without prefix

    Examples:
        "A) Machine Learning" -> "Machine Learning"
        "a. Neural Networks" -> "Neural Networks"
        "1) Deep Learning" -> "Deep Learning"
    """
    # Remove leading option markers
    patterns = [
        r'^[A-Da-d]\)\s*',  # A), B), etc.
        r'^[A-Da-d]\.\s*',  # A., B., etc.
        r'^[A-Da-d]\s*[-:]\s*',  # A -, A :, etc.
        r'^\d+\)\s*',  # 1), 2), etc.
        r'^\d+\.\s*',  # 1., 2., etc.
        r'^\([A-Da-d]\)\s*',  # (A), (B), etc.
    ]

    for pattern in patterns:
        text = re.sub(pattern, '', text)

    return text.strip()


def extract_correct_answer(text: str) -> Optional[str]:
    """
    Extract correct answer letter from text.

    Args:
        text: Text containing answer indication

    Returns:
        Single letter A/B/C/D or None if not found

    Examples:
        "Answer: A" -> "A"
        "Correct answer is B" -> "B"
        "(C)" -> "C"
        "The answer is option D" -> "D"
    """
    # Common patterns for answer indication
    patterns = [
        r'(?:answer|correct|solution)(?:\s+is)?:?\s*([A-Da-d])',
        r'\b([A-Da-d])\s+is\s+(?:the\s+)?correct',
        r'\(([A-Da-d])\)',
        r'option\s+([A-Da-d])',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()

    # If just a single letter A-D
    match = re.search(r'\b([A-Da-d])\b', text)
    if match:
        return match.group(1).upper()

    return None


def truncate_text(text: str, max_length: int = 500, suffix: str = '...') -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def is_valid_mcq_question(text: str) -> bool:
    """
    Check if text looks like a valid MCQ question.

    Args:
        text: Question text

    Returns:
        True if valid, False otherwise

    Validation criteria:
    - Not empty
    - Minimum length (10 characters)
    - Contains question mark or question keywords
    """
    if not text or len(text.strip()) < 10:
        return False

    # Check for question patterns
    question_patterns = [
        r'\?',  # Question mark
        r'\bwhat\b',
        r'\bwhy\b',
        r'\bhow\b',
        r'\bwhich\b',
        r'\bwhere\b',
        r'\bwhen\b',
        r'\bwho\b',
        r'\bdefine\b',
        r'\bexplain\b',
        r'\bidentify\b',
    ]

    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in question_patterns)
