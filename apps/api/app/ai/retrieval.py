from app.ai.embeddings import embed_text
from app.ai.security import filter_chunks_by_score
from app.ai.vector_store import search_similar
from app.core.config import settings


def retrieve_chunks(
    query: str,
    top_k: int = 3,
    organization_id: str | None = None,
    min_score: float | None = None
) -> list[dict]:
    """
    Retrieve similar chunks for a given query with security filtering.
    
    Args:
        query: User query text
        top_k: Number of results to return
        organization_id: Organization ID for multi-tenant isolation
        min_score: Minimum similarity score threshold (uses config default if None)
        
    Returns:
        List of similar chunks with text, metadata, and scores
        Only returns chunks that meet the similarity threshold
        
    Security:
        - Filters results by similarity score to prevent irrelevant context
        - Enforces organization boundaries for multi-tenant isolation
        - Returns empty list if no chunks meet threshold
    """
    try:
        # Validate input
        if not query or not query.strip():
            return []
        
        # Generate query embedding
        query_embedding = embed_text(query)
        
        # Call vector search with organization isolation
        results = search_similar(
            query_embedding,
            top_k,
            organization_id=organization_id or settings.default_organization_id
        )
        
        # Format output
        output = []
        for result in results:
            output.append({
                "text": result["text"],
                "document_id": result["document_id"],
                "organization_id": result["organization_id"],
                "chunk_index": result["chunk_index"],
                "chunk_id": result["chunk_id"],
                "page_number": result["page_number"],
                "score": result["score"]
            })
        
        # Apply similarity threshold filtering
        threshold = min_score if min_score is not None else settings.retrieval_min_score
        filtered_output = filter_chunks_by_score(output, threshold)
        
        return filtered_output
        
    except Exception as e:
        # Return empty list on error
        return []

# Made with Bob
