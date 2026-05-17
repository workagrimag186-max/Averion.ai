from app.ai.embeddings import embed_text
from app.ai.vector_store import search_similar


def retrieve_chunks(query: str, top_k: int = 3) -> list[dict]:
    """
    Retrieve similar chunks for a given query.
    
    Args:
        query: User query text
        top_k: Number of results to return
        
    Returns:
        List of similar chunks with text, metadata, and scores
    """
    try:
        # Validate input
        if not query or not query.strip():
            return []
        
        # Generate query embedding
        query_embedding = embed_text(query)
        
        # Call vector search
        results = search_similar(query_embedding, top_k)
        
        # Format output
        output = []
        for result in results:
            output.append({
                "text": result["text"],
                "document_id": result["document_id"],
                "chunk_index": result["chunk_index"],
                "page_number": result["page_number"],
                "score": result["score"]
            })
        
        return output
        
    except Exception as e:
        # Return empty list on error
        return []

# Made with Bob
