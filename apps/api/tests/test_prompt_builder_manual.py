"""
Manual test for RAG Prompt Builder

Run this file directly to test the build_rag_prompt function.
"""

import sys
from pathlib import Path

# Add parent directory to path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.prompt_builder import build_rag_prompt


def test_with_multiple_chunks():
    """Test prompt building with multiple chunks."""
    print("=" * 80)
    print("TEST 1: Multiple Chunks")
    print("=" * 80)

    # Create fake chunks
    chunks = [
        {
            "document_id": "doc1",
            "chunk_index": 0,
            "chunk_id": "doc1_0",
            "text": "FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints."
        },
        {
            "document_id": "doc1",
            "chunk_index": 1,
            "chunk_id": "doc1_1",
            "text": "Python is a high-level, interpreted programming language known for its simplicity and readability."
        },
        {
            "document_id": "doc2",
            "chunk_index": 0,
            "chunk_id": "doc2_0",
            "text": "Type hints in Python allow developers to specify the expected data types of function parameters and return values."
        }
    ]

    question = "What is FastAPI?"

    # Build prompt
    prompt = build_rag_prompt(question, chunks)

    # Print output
    print("\nGenerated Prompt:")
    print("-" * 80)
    print(prompt)
    print("-" * 80)

    # Verify requirements
    print("\nVerification:")
    print(f"[PASS] Context included: {'Context:' in prompt}")
    print(f"[PASS] Question included: {question in prompt}")
    print(f"[PASS] Citations format exists: {'[doc1_0]' in prompt}")
    print(f"[PASS] Instructions present: {'Use ONLY the context below' in prompt}")
    print(f"[PASS] All chunks present: {all(chunk['chunk_id'] in prompt for chunk in chunks)}")
    print(f"[PASS] Answer section exists: {'Answer (with citations):' in prompt}")


def test_with_empty_chunks():
    """Test prompt building with empty chunks list."""
    print("\n" + "=" * 80)
    print("TEST 2: Empty Chunks")
    print("=" * 80)

    chunks = []
    question = "What is FastAPI?"

    # Build prompt
    prompt = build_rag_prompt(question, chunks)

    # Print output
    print("\nGenerated Prompt:")
    print("-" * 80)
    print(prompt)
    print("-" * 80)

    # Verify requirements
    print("\nVerification:")
    print(f"[PASS] No context message: {'No relevant context provided.' in prompt}")
    print(f"[PASS] Question included: {question in prompt}")
    print(f"[PASS] Instructions present: {'Use ONLY the context below' in prompt}")


def test_with_single_chunk():
    """Test prompt building with a single chunk."""
    print("\n" + "=" * 80)
    print("TEST 3: Single Chunk")
    print("=" * 80)

    chunks = [
        {
            "document_id": "doc1",
            "chunk_index": 0,
            "chunk_id": "doc1_0",
            "text": "FastAPI is a modern web framework for building APIs with Python."
        }
    ]

    question = "What is FastAPI?"

    # Build prompt
    prompt = build_rag_prompt(question, chunks)

    # Print output
    print("\nGenerated Prompt:")
    print("-" * 80)
    print(prompt)
    print("-" * 80)

    # Verify requirements
    print("\nVerification:")
    print(f"[PASS] Context included: {'Context:' in prompt}")
    print(f"[PASS] Question included: {question in prompt}")
    print(f"[PASS] Citation format: {'[doc1_0]' in prompt}")
    print(f"[PASS] Chunk metadata: {'(doc: doc1, chunk: 0)' in prompt}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("RAG PROMPT BUILDER - MANUAL TEST")
    print("=" * 80)

    test_with_multiple_chunks()
    test_with_empty_chunks()
    test_with_single_chunk()

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)

# Made with Bob
