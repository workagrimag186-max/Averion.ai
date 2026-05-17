import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """
    Lazily load the embedding model.

    Keeping model loading out of module import makes tests and app startup safer.
    The first embedding call may still download/load the model.
    """
    global _model

    if _model is None:
        logger.info("Loading embedding model: %s", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)

    return _model


def embed_text(text: str) -> list[float]:
    """
    Generate embedding for a single text string.
    
    Args:
        text: Input text to embed
        
    Returns:
        List of floats representing the embedding vector
    """
    embedding = get_embedding_model().encode(text)
    return embedding.tolist()


def generate_embeddings(chunks: list[dict]) -> list[dict]:
    """
    Generate embeddings for each document chunk and attach them to the chunk data.
    
    Args:
        chunks: List of chunk dictionaries containing document_id, chunk_index, 
                page_number, and text
                
    Returns:
        Updated list of chunks with embeddings attached
    """
    processed_count = 0
    failed_count = 0
    
    logger.info(
        "Starting embedding generation for %s chunks using %s",
        len(chunks),
        MODEL_NAME
    )
    
    for chunk in chunks:
        try:
            # Skip empty text
            text = chunk.get("text", "")
            if not text or not text.strip():
                logger.warning(f"Skipping chunk {chunk.get('chunk_index')} - empty text")
                failed_count += 1
                continue
            
            # Generate embedding
            embedding = embed_text(text)
            chunk["embedding"] = embedding
            processed_count += 1
            
        except Exception as e:
            logger.error(
                f"Failed to generate embedding for chunk {chunk.get('chunk_index')}: {str(e)}"
            )
            failed_count += 1
            continue
    
    logger.info(
        f"Embedding generation complete. "
        f"Processed: {processed_count}, Failed: {failed_count}, "
        f"Model: {MODEL_NAME}"
    )
    
    return chunks

# Made with Bob
