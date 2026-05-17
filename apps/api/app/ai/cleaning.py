"""
Text cleaning utilities for document processing.

Provides functions to clean and normalize text before chunking,
removing noise while preserving content structure and readability.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Clean and normalize text for processing.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text with normalized whitespace and reduced noise
    """
    # Handle None or empty input
    if text is None or not text:
        return ""
    
    # Convert to string if not already
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception as e:
            logger.warning(f"Failed to convert input to string: {e}")
            return ""
    
    # Remove null bytes and other control characters (except newlines and tabs)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize line endings to \n
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove repeated separator lines (e.g., ----, ****, ====, ____) 
    # Only if they span most of a line (4+ repetitions)
    text = re.sub(r'^[-*=_]{4,}\s*$', '', text, flags=re.MULTILINE)
    
    # Remove excessive blank lines (3+ consecutive newlines -> 2 newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Normalize horizontal whitespace
    # Replace tabs with spaces
    text = text.replace('\t', ' ')
    
    # Remove trailing whitespace from each line
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    
    # Collapse multiple spaces into single space (but preserve line structure)
    text = re.sub(r'[ ]{2,}', ' ', text)
    
    # Remove leading whitespace from each line (but preserve paragraph structure)
    text = re.sub(r'^[ ]+', '', text, flags=re.MULTILINE)
    
    # Strip leading and trailing whitespace from entire text
    text = text.strip()
    
    # Final check: if result is empty or only whitespace, return empty string
    if not text or text.isspace():
        return ""
    
    return text

# Made with Bob
