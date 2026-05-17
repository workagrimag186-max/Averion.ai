"""
Ingestion pipeline for document processing.

Orchestrates the full pipeline: extraction → cleaning → chunking
"""

from typing import Optional
from .extraction import extract_text
from .cleaning import clean_text
from .chunking import chunk_text


def run_ingestion_pipeline(
    file_path: str,
    file_type: str,
    document_id: str,
    page_number: Optional[int] = None
) -> list[dict]:
    """
    Run the full ingestion pipeline on a document.
    
    Args:
        file_path: Path to the file to process
        file_type: Type of file (txt, pdf, docx)
        document_id: Unique identifier for the document
        page_number: Optional page number for metadata
        
    Returns:
        List of chunk dictionaries with metadata, or empty list on failure
    """
    # Step 1: Extract text
    extracted_text = extract_text(file_path, file_type)
    if not extracted_text:
        return []
    
    # Step 2: Clean text
    cleaned_text = clean_text(extracted_text)
    if not cleaned_text:
        return []
    
    # Step 3: Chunk text
    chunks = chunk_text(cleaned_text, document_id, page_number)
    if not chunks:
        return []
    
    return chunks

# Made with Bob