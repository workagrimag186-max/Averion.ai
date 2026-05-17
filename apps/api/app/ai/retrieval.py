import logging
from sentence_transformers import SentenceTransformer
from app.ai.vector_store import search_similar

logger = logging.getLogger(__name__)

# Load model globally
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def retrieve_chunks(query: str, top_k: int = 3) -> list[dict]:
    """
    Retrieve the most relevant document chunks for a given query.
    
    Args:
        query: User question or search query
        top_k: Number of top results to return (default: 3)
        
    Returns:
        List of dictionaries containing:
            - text: chunk text
            - document_id: document identifier
            - chunk_index: chunk position in document
            - page_number: page number in document
            - score: similarity score
    """
    # Validate input
    if not query or not query.strip():
        logger.warning("Empty query received")
        return []
    
    logger.info(f"Retrieval query received: '{query}' (top_k={top_k})")
    
    try:
        # Generate query embedding
        query_embedding = model.encode(query)
        
        # Search vector database
        results = search_similar(query_embedding.tolist(), top_k)
        
        # Format output
        formatted_results = []
        for result in results:
            formatted_result = {
                "text": result["text"],
                "document_id": result["metadata"]["document_id"],
                "chunk_index": result["metadata"]["chunk_index"],
                "page_number": result["metadata"]["page_number"],
                "score": result["score"]
            }
            formatted_results.append(formatted_result)
        
        logger.info(f"Retrieved {len(formatted_results)} results")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error during retrieval: {e}")
        return []

# Made with Bob