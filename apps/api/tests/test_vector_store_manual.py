"""
Manual test for vector store functionality.
Run with: python apps/api/tests/test_vector_store_manual.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.ai.embeddings import generate_embeddings
from app.ai.vector_store import store_embeddings, search_similar


class FakeEmbedding:
    def __init__(self, values: list[float]):
        self.values = values

    def tolist(self) -> list[float]:
        return self.values


class FakeEmbeddingModel:
    def encode(self, text: str) -> FakeEmbedding:
        lower_text = text.lower()
        if "fastapi" in lower_text:
            return FakeEmbedding([1.0, 0.0, 0.0])
        if "python" in lower_text:
            return FakeEmbedding([0.0, 1.0, 0.0])
        if "machine learning" in lower_text:
            return FakeEmbedding([0.0, 0.0, 1.0])
        return FakeEmbedding([0.5, 0.5, 0.5])


def test_vector_store(monkeypatch):
    """Test storing and searching embeddings."""
    monkeypatch.setattr("app.ai.embeddings._model", FakeEmbeddingModel())
    
    print("=" * 60)
    print("VECTOR STORE TEST")
    print("=" * 60)
    
    # Create sample chunks without embeddings
    chunks = [
        {
            "document_id": "doc1",
            "chunk_index": 0,
            "page_number": 1,
            "text": "FastAPI is a modern web framework for building APIs"
        },
        {
            "document_id": "doc1",
            "chunk_index": 1,
            "page_number": 1,
            "text": "Python is a high-level programming language"
        },
        {
            "document_id": "doc2",
            "chunk_index": 0,
            "page_number": 1,
            "text": "Machine learning models require training data"
        },
        {
            "document_id": "doc2",
            "chunk_index": 1,
            "page_number": 2,
            "text": "Vector databases store embeddings efficiently"
        }
    ]
    
    print(f"\n1. Generating embeddings for {len(chunks)} chunks...")
    chunks = generate_embeddings(chunks)
    print("   [OK] Embeddings generated")
    
    print(f"\n2. Storing {len(chunks)} chunks...")
    store_embeddings(chunks, clear_existing=True)
    print("   [OK] Chunks stored successfully")
    
    # Query with embedding from first chunk
    print("\n3. Searching for similar chunks...")
    query_embedding = chunks[0]["embedding"]
    results = search_similar(query_embedding, top_k=2)
    
    print(f"   [OK] Found {len(results)} results")
    
    # Verify results
    print("\n4. Verifying results...")
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
