"""
Citation mapping module for enriching retrieved chunks with metadata.

This module provides functionality to map retrieved chunks to rich citation objects
by fetching additional metadata (filename, page_number) from the database.
"""

import psycopg

from app.core.config import settings
from app.db.connection import is_database_configured


def fetch_chunk_metadata(chunks: list[dict]) -> dict[tuple[str, int], dict]:
    """
    Fetch metadata for chunks from database in a single batch query.
    
    Args:
        chunks: List of chunk dictionaries with document_id and chunk_index
        
    Returns:
        Dictionary mapping (document_id, chunk_index) to metadata dict containing:
        - filename: str
        - page_number: int | None
        
    Note:
        Uses efficient batch query to avoid N+1 problem.
        Returns empty dict if database is not configured.
    """
    if not chunks:
        return {}
    
    if not is_database_configured():
        return {}
    
    try:
        # Extract unique (document_id, chunk_index) pairs
        chunk_keys = set()
        for chunk in chunks:
            doc_id = chunk.get("document_id")
            chunk_idx = chunk.get("chunk_index")
            if doc_id is not None and chunk_idx is not None:
                chunk_keys.add((str(doc_id), int(chunk_idx)))
        
        if not chunk_keys:
            return {}
        
        # Build batch query using ANY for efficient lookup
        document_ids = list(set(doc_id for doc_id, _ in chunk_keys))
        
        with psycopg.connect(settings.database_url, connect_timeout=5) as connection:  # type: ignore
            with connection.cursor() as cursor:
                # Fetch all needed data in one query with JOIN
                cursor.execute(
                    """
                    SELECT 
                        dc.document_id::text,
                        dc.chunk_index,
                        d.filename,
                        dc.page_number
                    FROM document_chunks dc
                    INNER JOIN documents d ON d.id = dc.document_id
                    WHERE dc.document_id = ANY(%s::uuid[])
                    """,
                    (document_ids,)
                )
                
                # Build lookup dictionary
                metadata_map = {}
                for row in cursor.fetchall():
                    doc_id, chunk_idx, filename, page_num = row
                    metadata_map[(doc_id, chunk_idx)] = {
                        "filename": filename,
                        "page_number": page_num
                    }
                
                return metadata_map
                
    except Exception as e:
        # Log error but don't fail - return empty dict
        print(f"Warning: Failed to fetch chunk metadata: {e}")
        return {}


def build_citations(chunks: list[dict]) -> list[dict]:
    """
    Build rich citation objects from retrieved chunks.
    
    Enriches each chunk with metadata from the database:
    - Uses existing chunk_id if present, otherwise constructs from document_id and chunk_index
    - Uses existing filename if present, otherwise fetches from documents table
    - Uses existing page_number if present, otherwise fetches from document_chunks table
    - Creates snippet from chunk text (first ~200 characters)
    
    Args:
        chunks: List of chunk dictionaries from retrieval, each containing:
            - document_id: str
            - chunk_index: int
            - text: str
            - score: float (optional)
            - chunk_id: str (optional, will be constructed if missing)
            - filename: str (optional, will be fetched if missing)
            - page_number: int | None (optional, will be fetched if missing)
            
    Returns:
        List of citation dictionaries, each containing:
            - chunk_id: str
            - document_id: str
            - chunk_index: int
            - filename: str
            - page_number: int | None
            - snippet: str (first ~200 chars of text)
            - score: float | None
            
    Note:
        - Preserves existing metadata from chunks (e.g., from mocks or pre-enriched data)
        - Only fetches from database if metadata is missing
        - Handles missing database rows gracefully (uses fallback values)
        - Returns empty list if input is empty
        - Avoids N+1 queries by fetching all metadata in one batch
    """
    if not chunks:
        return []
    
    # Check which chunks need metadata from database
    chunks_needing_metadata = []
    for chunk in chunks:
        # Only fetch if filename or page_number is missing
        if "filename" not in chunk or "page_number" not in chunk:
            chunks_needing_metadata.append(chunk)
    
    # Fetch metadata only for chunks that need it
    metadata_map = {}
    if chunks_needing_metadata:
        metadata_map = fetch_chunk_metadata(chunks_needing_metadata)
    
    citations = []
    for chunk in chunks:
        try:
            document_id = chunk.get("document_id", "unknown")
            chunk_index = chunk.get("chunk_index", 0)
            text = chunk.get("text", "")
            score = chunk.get("score")
            
            # Use existing chunk_id if present, otherwise construct it
            chunk_id = chunk.get("chunk_id")
            if not chunk_id:
                chunk_id = f"{document_id}:{chunk_index}"
            
            # Use existing filename if present, otherwise get from metadata or fallback
            filename = chunk.get("filename")
            if not filename:
                metadata = metadata_map.get((str(document_id), int(chunk_index)), {})
                filename = metadata.get("filename", document_id)
            
            # Use existing page_number if present, otherwise get from metadata
            page_number = chunk.get("page_number")
            if page_number is None and (str(document_id), int(chunk_index)) in metadata_map:
                metadata = metadata_map.get((str(document_id), int(chunk_index)), {})
                page_number = metadata.get("page_number")
            
            # Create snippet (first ~200 characters, safe truncation)
            snippet = text[:200] if text else ""
            
            citations.append({
                "chunk_id": chunk_id,
                "document_id": document_id,
                "chunk_index": chunk_index,
                "filename": filename,
                "page_number": page_number,
                "snippet": snippet,
                "score": score
            })
            
        except Exception as e:
            # Skip malformed chunks but log the error
            print(f"Warning: Failed to build citation for chunk: {e}")
            continue
    
    return citations


# Made with Bob
