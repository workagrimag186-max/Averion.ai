from app.ai.embeddings import generate_embeddings
from app.ai.vector_store import build_chunk_id
from app.ai.vector_store import store_embeddings
from app.ai.retrieval import retrieve_chunks


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
        return FakeEmbedding([0.0, 0.0, 1.0])


def test_retrieval(monkeypatch):
    """Test retrieval service with sample chunks."""
    monkeypatch.setattr("app.ai.embeddings._model", FakeEmbeddingModel())
    monkeypatch.setattr("app.ai.vector_store.is_database_configured", lambda: False)
    
    # Prepare sample chunks without embeddings
    chunks = [
        {
            "document_id": "doc1",
            "organization_id": "org-retrieval",
            "chunk_index": 0,
            "page_number": 1,
            "text": "FastAPI is a web framework"
        },
        {
            "document_id": "doc1",
            "organization_id": "org-retrieval",
            "chunk_index": 1,
            "page_number": 1,
            "text": "Python is used for AI"
        }
    ]
    
    # Generate real embeddings
    chunks = generate_embeddings(chunks)
    
    # Store embeddings
    store_embeddings(chunks, clear_existing=True)
    
    # Query
    query = "What is FastAPI?"
    results = retrieve_chunks(query, top_k=2, organization_id="org-retrieval")
    
    # Verify
    assert len(results) > 0, "No results returned"
    
    for result in results:
        assert "text" in result, "Missing text field"
        assert "document_id" in result, "Missing document_id field"
        assert "organization_id" in result, "Missing organization_id field"
        assert "chunk_index" in result, "Missing chunk_index field"
        assert "chunk_id" in result, "Missing chunk_id field"
        assert "page_number" in result, "Missing page_number field"
        assert "score" in result, "Missing score field"
        assert result["chunk_id"] == build_chunk_id(
            result["document_id"],
            result["chunk_index"]
        )
        assert result["organization_id"] == "org-retrieval"
    
    # Print results
    print(f"\nQuery: {query}")
    print(f"Number of results: {len(results)}")
    print(f"First result preview:")
    print(f"  Text: {results[0]['text']}")
    print(f"  Document ID: {results[0]['document_id']}")
    print(f"  Chunk ID: {results[0]['chunk_id']}")
    print(f"  Score: {results[0]['score']}")
    
    print("\n✅ Retrieval test passed!")


if __name__ == "__main__":
    test_retrieval()

# Made with Bob
