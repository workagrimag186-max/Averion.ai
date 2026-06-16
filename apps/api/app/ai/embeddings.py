import logging
import os
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

MODEL_NAME = settings.embedding_model_name
_model: Any | None = None
_model_error: str | None = None


def get_embedding_model() -> Any:
    """
    Lazily load the embedding model.

    Keeping model loading out of module import makes tests and app startup safer.
    The first embedding call may still download/load the model.
    """
    global _model, _model_error

    if _model is None:
        # Keep the local AI stack friendly to laptops with limited memory.
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        os.environ.setdefault("OMP_NUM_THREADS", "2")
        os.environ.setdefault("MKL_NUM_THREADS", "2")

        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", MODEL_NAME)
        try:
            _model = SentenceTransformer(MODEL_NAME, local_files_only=True)
        except OSError:
            logger.info(
                "Embedding model is not cached; downloading %s",
                MODEL_NAME
            )
            _model = SentenceTransformer(MODEL_NAME)
        _model_error = None

    return _model


def preload_embedding_model() -> bool:
    """Load the embedding model during startup when configured."""
    global _model_error
    try:
        get_embedding_model()
        return True
    except Exception as exc:
        _model_error = type(exc).__name__
        logger.exception("Embedding model preload failed")
        return False


def get_embedding_model_status() -> dict[str, str | bool | None]:
    return {
        "model": MODEL_NAME,
        "loaded": _model is not None,
        "error": _model_error
    }


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


def generate_embeddings(
    chunks: list[dict],
    batch_size: int | None = None
) -> list[dict]:
    """
    Generate embeddings for each document chunk and attach them to the chunk data.
    
    Args:
        chunks: List of chunk dictionaries containing document_id, chunk_index, 
                page_number, and text
                
    Returns:
        Updated list of chunks with embeddings attached
    """
    eligible_chunks = [
        chunk
        for chunk in chunks
        if str(chunk.get("text", "")).strip()
    ]
    failed_count = len(chunks) - len(eligible_chunks)
    
    logger.info(
        "Starting embedding generation for %s chunks using %s",
        len(chunks),
        MODEL_NAME
    )
    
    if not eligible_chunks:
        return chunks

    model = get_embedding_model()
    texts = [str(chunk["text"]).strip() for chunk in eligible_chunks]
    embeddings = model.encode(
        texts,
        batch_size=batch_size or settings.embedding_batch_size,
        show_progress_bar=False
    )

    for chunk, embedding in zip(eligible_chunks, embeddings):
        chunk["embedding"] = embedding.tolist()
    
    logger.info(
        f"Embedding generation complete. "
        f"Processed: {len(eligible_chunks)}, Failed: {failed_count}, "
        f"Model: {MODEL_NAME}"
    )
    
    return chunks
