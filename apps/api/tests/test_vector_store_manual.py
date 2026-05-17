"""
Manual test for vector store functionality.
Run with: python apps/api/tests/test_vector_store_manual.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from apps.api.app.ai.vector_store import store_embeddings, search_similar


def test_vector_store():
    """Test storing and searching embeddings."""
    
    print("=" * 60)
    print("VECTOR STORE TEST")
    print("=" * 60)
    
    # Create sample chunks with small fake embeddings
    chunks = [
        {
            "document_id": "doc1",
            "chunk_index": 0,
            "page_number": 1,
            "text": "FastAPI is a modern web framework for building APIs",
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        },
        {
            "document_id": "doc1",
            "chunk_index": 1,
            "page_number": 1,
            "text": "Python is a high-level programming language",
            "embedding": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        },
        {
            "document_id": "doc2",
            "chunk_index": 0,
            "page_number": 1,
            "text": "Machine learning models require training data",
            "embedding": [0.5, 0.6, 0.7, 0.8, 0.1, 0.2, 0.3, 0.4]
        },
        {
            "document_id": "doc2",
            "chunk_index": 1,
            "page_number": 2,
            "text": "Vector databases store embeddings efficiently",
            "embedding": [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.1]
        }
    ]
    
    print(f"\n1. Storing {len(chunks)} chunks...")
    store_embeddings(chunks)
    print("   [OK] Chunks stored successfully")
    
    # Query with embedding similar to first chunk
    print("\n2. Searching for similar chunks...")
    query_embedding = [0.1, 0.2, 0.25, 0.4, 0.5, 0.6, 0.7, 0.75]
    results = search_similar(query_embedding, top_k=2)
    
    print(f"   [OK] Found {len(results)} results")
    
    # Verify results
    print("\n3. Verifying results...")
    assert len(results) > 0, "No results returned"
    print(f"   [OK] Results count: {len(results)}")
    
    for i, result in enumerate(results):
        print(f"\n   Result {i + 1}:")
        assert "text" in result, "Missing 'text' field"
        assert "document_id" in result, "Missing 'document_id' field"
        assert "chunk_index" in result, "Missing 'chunk_index' field"
        assert "page_number" in result, "Missing 'page_number' field"
        assert "score" in result, "Missing 'score' field"
        
        print(f"     - Document ID: {result['document_id']}")
        print(f"     - Chunk Index: {result['chunk_index']}")
        print(f"     - Page Number: {result['page_number']}")
        print(f"     - Score: {result['score']:.4f}")
        print(f"     - Text: {result['text'][:60]}...")
    
    print("\n" + "=" * 60)
    print("TOP RESULT PREVIEW")
    print("=" * 60)
    top_result = results[0]
    print(f"Document ID: {top_result['document_id']}")
    print(f"Chunk Index: {top_result['chunk_index']}")
    print(f"Page Number: {top_result['page_number']}")
    print(f"Similarity Score: {top_result['score']:.4f}")
    print(f"Text: {top_result['text']}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_vector_store()

# Made with Bob
