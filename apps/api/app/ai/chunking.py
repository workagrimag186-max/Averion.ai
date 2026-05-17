"""
Text chunking module for splitting cleaned text into overlapping chunks.
"""

import re
from typing import Optional


def chunk_text(
    text: str,
    document_id: str,
    page_number: Optional[int] = None
) -> list[dict]:
    """
    Split text into overlapping chunks with approximate token limits.
    
    Args:
        text: Cleaned text to chunk
        document_id: Document identifier
        page_number: Optional page number
        
    Returns:
        List of chunk dictionaries with metadata
    """
    # Configuration
    MIN_CHUNK_SIZE = 600  # tokens (approx words)
    MAX_CHUNK_SIZE = 900  # tokens (approx words)
    OVERLAP_SIZE = 125    # tokens (approx words)
    
    # Split into sentences (simple approach)
    sentences = _split_into_sentences(text)
    
    if not sentences:
        return []
    
    chunks = []
    chunk_index = 0
    current_chunk = []
    current_size = 0
    overlap_buffer = []
    
    for sentence in sentences:
        sentence_size = _estimate_tokens(sentence)
        
        # Check if adding this sentence exceeds max size
        if current_size + sentence_size > MAX_CHUNK_SIZE and current_chunk:
            # Finalize current chunk
            chunk_text = " ".join(current_chunk).strip()
            if chunk_text:
                chunks.append({
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "page_number": page_number,
                    "text": chunk_text
                })
                chunk_index += 1
            
            # Prepare overlap buffer for next chunk
            overlap_buffer = _get_overlap_sentences(current_chunk, OVERLAP_SIZE)
            
            # Start new chunk with overlap
            current_chunk = overlap_buffer + [sentence]
            current_size = sum(_estimate_tokens(s) for s in current_chunk)
        else:
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_size += sentence_size
    
    # Add final chunk if it exists
    if current_chunk:
        chunk_text = " ".join(current_chunk).strip()
        if chunk_text:
            chunks.append({
                "document_id": document_id,
                "chunk_index": chunk_index,
                "page_number": page_number,
                "text": chunk_text
            })
    
    return chunks


def _split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences using simple regex patterns.
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    # Simple sentence boundary detection
    # Matches periods, question marks, exclamation marks followed by space/newline
    pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    
    sentences = re.split(pattern, text)
    
    # Filter out empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def _estimate_tokens(text: str) -> int:
    """
    Estimate token count by splitting on whitespace.
    
    Args:
        text: Input text
        
    Returns:
        Approximate token count
    """
    return len(text.split())


def _get_overlap_sentences(sentences: list[str], target_overlap: int) -> list[str]:
    """
    Get sentences from end of chunk to create overlap.
    
    Args:
        sentences: List of sentences in current chunk
        target_overlap: Target overlap size in tokens
        
    Returns:
        List of sentences for overlap
    """
    overlap = []
    overlap_size = 0
    
    # Work backwards from end of chunk
    for sentence in reversed(sentences):
        sentence_size = _estimate_tokens(sentence)
        if overlap_size + sentence_size <= target_overlap:
            overlap.insert(0, sentence)
            overlap_size += sentence_size
        else:
            break
    
    return overlap

# Made with Bob
