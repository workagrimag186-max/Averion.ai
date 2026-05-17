from sentence_transformers import SentenceTransformer
from app.ai.vector_store import search_similar

# Load model globally
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


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
        query_embedding = model.encode(query)
        
        # Call vector search
        results = search_similar(query_embedding.tolist(), top_k)
        
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
