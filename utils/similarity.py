"""
Similarity calculation and deduplication algorithms.
"""

import hashlib
from difflib import SequenceMatcher
from typing import Tuple
import re


def calculate_similarity_hash(text: str) -> str:
    """
    Generate MD5 hash for exact duplicate detection.

    Args:
        text: Text to hash

    Returns:
        MD5 hash string

    Note: Text is normalized before hashing
    """
    from utils.text_processor import normalize_text

    normalized = normalize_text(text)
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


def fuzzy_match(text1: str, text2: str) -> float:
    """
    Calculate similarity score between two texts.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0.0 and 1.0

    Uses SequenceMatcher (Gestalt pattern matching) which considers:
    - Longest contiguous matching subsequence
    - Ratio of matching characters to total characters
    """
    from utils.text_processor import normalize_text

    # Normalize both texts
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)

    # Calculate similarity
    return SequenceMatcher(None, norm1, norm2).ratio()


def jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity between two texts (word-based).

    Args:
        text1: First text
        text2: Second text

    Returns:
        Jaccard similarity score between 0.0 and 1.0

    Jaccard similarity = |intersection| / |union|
    """
    from utils.text_processor import normalize_text

    # Normalize and split into words
    words1 = set(normalize_text(text1).split())
    words2 = set(normalize_text(text2).split())

    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0

    # Calculate Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def are_duplicates(text1: str, text2: str, threshold: float = 0.85) -> bool:
    """
    Check if two texts are duplicates based on similarity threshold.

    Args:
        text1: First text
        text2: Second text
        threshold: Similarity threshold (0.0 to 1.0)

    Returns:
        True if texts are duplicates, False otherwise

    Uses fuzzy matching with configurable threshold
    """
    return fuzzy_match(text1, text2) >= threshold


def get_similarity_metrics(text1: str, text2: str) -> dict:
    """
    Get multiple similarity metrics for two texts.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Dictionary with various similarity metrics

    Useful for debugging and fine-tuning thresholds
    """
    return {
        'fuzzy_match': fuzzy_match(text1, text2),
        'jaccard': jaccard_similarity(text1, text2),
        'hash_match': calculate_similarity_hash(text1) == calculate_similarity_hash(text2)
    }


def find_duplicates_in_list(texts: list, threshold: float = 0.85) -> list:
    """
    Find all duplicate pairs in a list of texts.

    Args:
        texts: List of text strings
        threshold: Similarity threshold

    Returns:
        List of tuples (index1, index2, similarity_score) for duplicates

    Note: This is O(n^2) and may be slow for large lists
    """
    duplicates = []

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            similarity = fuzzy_match(texts[i], texts[j])
            if similarity >= threshold:
                duplicates.append((i, j, similarity))

    return duplicates
