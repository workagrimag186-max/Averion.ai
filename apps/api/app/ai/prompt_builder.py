"""
RAG Prompt Builder

Builds structured prompts for LLM using retrieved document chunks.
"""


def build_rag_prompt(question: str, chunks: list[dict]) -> str:
    """
    Build a structured RAG prompt for an LLM.

    Args:
        question: User query string
        chunks: List of retrieved chunks, each containing:
            - document_id: str
            - chunk_index: int
            - chunk_id: str
            - text: str

    Returns:
        Formatted prompt string with instructions, context, and question

    Example:
        >>> chunks = [
        ...     {
        ...         "document_id": "doc1",
        ...         "chunk_index": 0,
        ...         "chunk_id": "doc1_0",
        ...         "text": "FastAPI is a modern web framework..."
        ...     }
        ... ]
        >>> prompt = build_rag_prompt("What is FastAPI?", chunks)
    """
    # Build the prompt header with clear instructions
    prompt_parts = [
        "You are a helpful AI assistant.",
        "",
        "Use ONLY the context below to answer the question.",
        "If the answer is not in the context, say you don't know.",
        "",
    ]

    # Add context section
    prompt_parts.append("Context:")

    if not chunks:
        # Handle empty chunks case
        prompt_parts.append("No relevant context provided.")
    else:
        # Add all chunks with proper formatting
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "unknown")
            document_id = chunk.get("document_id", "unknown")
            chunk_index = chunk.get("chunk_index", 0)
            text = chunk.get("text", "")

            # Format: [chunk_id] (doc: document_id, chunk: chunk_index)
            prompt_parts.append(f"[{chunk_id}] (doc: {document_id}, chunk: {chunk_index})")
            prompt_parts.append(text)
            prompt_parts.append("")  # Empty line between chunks

    # Add question section
    prompt_parts.extend([
        "Question:",
        question,
        "",
        "Answer (with citations):",
    ])

    # Join all parts with newlines
    return "\n".join(prompt_parts)

# Made with Bob
