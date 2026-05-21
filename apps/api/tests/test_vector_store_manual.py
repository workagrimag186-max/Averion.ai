"""
Manual test for vector store functionality.
Run with: python apps/api/tests/test_vector_store_manual.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.ai.embeddings import generate_embeddings
from app.ai.vector_store import build_chunk_id, store_embeddings, search_similar


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
            "organization_id": "org-vector",
            "chunk_index": 0,
            "page_number": 1,
            "text": "FastAPI is a modern web framework for building APIs"
        },
        {
            "document_id": "doc1",
            "organization_id": "org-vector",
            "chunk_index": 1,
            "page_number": 1,
            "text": "Python is a high-level programming language"
        },
        {
            "document_id": "doc2",
            "organization_id": "org-vector",
            "chunk_index": 0,
            "page_number": 1,
            "text": "Machine learning models require training data"
        },
        {
            "document_id": "doc2",
            "organization_id": "org-vector",
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
    results = search_similar(query_embedding, top_k=2, organization_id="org-vector")
    
    print(f"   [OK] Found {len(results)} results")
    
    # Verify results
    print("\n4. Verifying results...")
    assert len(results) > 0, "No results returned"
    print(f"   [OK] Results count: {len(results)}")
    
    for i, result in enumerate(results):
        print(f"\n   Result {i + 1}:")
        assert "text" in result, "Missing 'text' field"
        assert "document_id" in result, "Missing 'document_id' field"
        assert "organization_id" in result, "Missing 'organization_id' field"
        assert "chunk_index" in result, "Missing 'chunk_index' field"
        assert "chunk_id" in result, "Missing 'chunk_id' field"
        assert "page_number" in result, "Missing 'page_number' field"
        assert "score" in result, "Missing 'score' field"
        assert result["chunk_id"] == build_chunk_id(
            result["document_id"],
            result["chunk_index"]
        )
        assert result["organization_id"] == "org-vector"
        
        print(f"     - Document ID: {result['document_id']}")
        print(f"     - Chunk Index: {result['chunk_index']}")
        print(f"     - Chunk ID: {result['chunk_id']}")
        print(f"     - Page Number: {result['page_number']}")
        print(f"     - Score: {result['score']:.4f}")
        print(f"     - Text: {result['text'][:60]}...")
    
    print("\n" + "=" * 60)
    print("TOP RESULT PREVIEW")
    print("=" * 60)
    top_result = results[0]
    print(f"Document ID: {top_result['document_id']}")
    print(f"Chunk Index: {top_result['chunk_index']}")
    print(f"Chunk ID: {top_result['chunk_id']}")
    print(f"Page Number: {top_result['page_number']}")
    print(f"Similarity Score: {top_result['score']:.4f}")
    print(f"Text: {top_result['text']}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] ALL TESTS PASSED")
    print("=" * 60)


def test_vector_upsert_does_not_delete_existing_vectors(monkeypatch):
    monkeypatch.setattr("app.ai.embeddings._model", FakeEmbeddingModel())

    first_batch = generate_embeddings([
        {
            "document_id": "doc-upsert-a",
            "organization_id": "org-upsert",
            "chunk_index": 0,
            "page_number": None,
            "text": "FastAPI keeps APIs organized"
        }
    ])
    second_batch = generate_embeddings([
        {
            "document_id": "doc-upsert-b",
            "organization_id": "org-upsert",
            "chunk_index": 0,
            "page_number": None,
            "text": "Python is useful for AI services"
        }
    ])

    store_embeddings(first_batch, clear_existing=True)
    store_embeddings(second_batch)

    fastapi_results = search_similar(
        first_batch[0]["embedding"],
        top_k=5,
        organization_id="org-upsert"
    )
    python_results = search_similar(
        second_batch[0]["embedding"],
        top_k=5,
        organization_id="org-upsert"
    )

    assert any(result["document_id"] == "doc-upsert-a" for result in fastapi_results)
    assert any(result["document_id"] == "doc-upsert-b" for result in python_results)


def test_vector_search_filters_by_organization(monkeypatch):
    monkeypatch.setattr("app.ai.embeddings._model", FakeEmbeddingModel())

    chunks = generate_embeddings([
        {
            "document_id": "doc-org-a",
            "organization_id": "org-a",
            "chunk_index": 0,
            "page_number": None,
            "text": "FastAPI keeps APIs organized"
        },
        {
            "document_id": "doc-org-b",
            "organization_id": "org-b",
            "chunk_index": 0,
            "page_number": None,
            "text": "FastAPI keeps APIs organized"
        }
    ])

    store_embeddings(chunks, clear_existing=True)

    org_a_results = search_similar(chunks[0]["embedding"], top_k=5, organization_id="org-a")
    org_b_results = search_similar(chunks[0]["embedding"], top_k=5, organization_id="org-b")

    assert org_a_results
    assert org_b_results
    assert all(result["organization_id"] == "org-a" for result in org_a_results)
    assert all(result["organization_id"] == "org-b" for result in org_b_results)


if __name__ == "__main__":
    test_vector_store()

# Made with Bob
