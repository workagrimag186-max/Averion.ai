from app.ai.vector_store import store_embeddings
from app.ai.retrieval import retrieve_chunks


def test_retrieval():
    """Test retrieval service with sample chunks."""
    
    # Prepare sample chunks with embeddings
    chunks = [
        {
            "document_id": "doc1",
            "chunk_index": 0,
            "page_number": 1,
            "text": "FastAPI is a web framework",
            "embedding": [0.1, 0.2, 0.3, 0.4]
        },
        {
            "document_id": "doc1",
            "chunk_index": 1,
            "page_number": 1,
            "text": "Python is used for AI",
            "embedding": [0.2, 0.3, 0.4, 0.5]
        }
    ]
    
    # Store embeddings
    store_embeddings(chunks)
    
    # Query
    query = "What is FastAPI?"
    results = retrieve_chunks(query, top_k=2)
    
    # Verify
    assert len(results) > 0, "No results returned"
    
    for result in results:
        assert "text" in result, "Missing text field"
        assert "document_id" in result, "Missing document_id field"
        assert "chunk_index" in result, "Missing chunk_index field"
        assert "page_number" in result, "Missing page_number field"
        assert "score" in result, "Missing score field"
    
    # Print results
    print(f"\nQuery: {query}")
    print(f"Number of results: {len(results)}")
    print(f"First result preview:")
    print(f"  Text: {results[0]['text']}")
    print(f"  Document ID: {results[0]['document_id']}")
    print(f"  Score: {results[0]['score']}")
    
    print("\n✅ Retrieval test passed!")


if __name__ == "__main__":
    test_retrieval()

# Made with Bob
