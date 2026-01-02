"""
Utility functions for keyword processing.
"""

import re
from typing import List, Set


def normalize_keyword(keyword: str) -> str:
    """
    Normalize a single keyword.
    
    - Convert to lowercase
    - Strip whitespace
    - Remove leading/trailing special characters
    """
    if not keyword:
        return ""
    
    # Convert to string and strip
    keyword = str(keyword).strip()
    
    # Skip empty strings
    if not keyword:
        return ""
    
    # Convert to lowercase for consistency
    keyword = keyword.lower()
    
    # Remove leading/trailing special characters (but keep internal ones)
    keyword = keyword.strip(".,!?;:")
    
    return keyword


def normalize_keywords(keywords: List[str]) -> List[str]:
    """
    Normalize a list of keywords.
    
    Args:
        keywords: List of keyword strings
        
    Returns:
        List of normalized keywords (empty strings removed)
    """
    normalized = []
    
    for keyword in keywords:
        normalized_keyword = normalize_keyword(keyword)
        if normalized_keyword:
            normalized.append(normalized_keyword)
    
    return normalized


def deduplicate_keywords(keywords: List[str], preserve_order: bool = True) -> List[str]:
    """
    Remove duplicate keywords.
    
    Args:
        keywords: List of keyword strings
        preserve_order: If True, preserve order of first occurrence
        
    Returns:
        Deduplicated list
    """
    if not preserve_order:
        return list(set(keywords))
    
    seen: Set[str] = set()
    unique = []
    
    for keyword in keywords:
        normalized = normalize_keyword(keyword)
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(keyword)  # Keep original casing for first occurrence
    
    return unique


def clean_keyword(keyword: str) -> str:
    """
    Clean a keyword by removing unwanted characters.
    
    Args:
        keyword: Raw keyword string
        
    Returns:
        Cleaned keyword
    """
    if not keyword:
        return ""
    
    # Remove hashtag symbol if at start
    keyword = keyword.lstrip("#")
    
    # Normalize whitespace
    keyword = " ".join(keyword.split())
    
    # Remove control characters
    keyword = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', keyword)
    
    return normalize_keyword(keyword)

