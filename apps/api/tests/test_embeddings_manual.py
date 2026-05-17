import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.embeddings import generate_embeddings


def test_embeddings():
    """Test embedding generation for document chunks."""
    
    # Sample chunk list
    chunks = [
        {
            "document_id": "doc1",
            "chunk_index": 0,
            "page_number": 1,
            "text": "FastAPI is a modern web framework"
        },
        {
            "document_id": "doc1",
            "chunk_index": 1,
            "page_number": 1,
            "text": "Python is a versatile programming language"
        },
        {
            "document_id": "doc1",
            "chunk_index": 2,
            "page_number": 2,
            "text": "Machine learning enables intelligent applications"
        }
    ]
    
    print("=" * 60)
    print("EMBEDDING GENERATION TEST")
    print("=" * 60)
    print(f"\nInput: {len(chunks)} chunks")
    
    # Generate embeddings
    result = generate_embeddings(chunks)
    
    # Verify results
    print(f"\n[PASS] Chunks processed: {len(result)}")
    
    successful_embeddings = 0
    embedding_dimension = None
    
    for i, chunk in enumerate(result):
        # Check if embedding exists
        assert "embedding" in chunk, f"Chunk {i} missing embedding"
        
        # Check if embedding is a list
        assert isinstance(chunk["embedding"], list), f"Chunk {i} embedding is not a list"
        
        # Check if length > 0
        assert len(chunk["embedding"]) > 0, f"Chunk {i} embedding is empty"
        
        # Get embedding dimension
        if embedding_dimension is None:
            embedding_dimension = len(chunk["embedding"])
        
        # Verify metadata is preserved
        assert "document_id" in chunk, f"Chunk {i} missing document_id"
        assert "chunk_index" in chunk, f"Chunk {i} missing chunk_index"
        assert "page_number" in chunk, f"Chunk {i} missing page_number"
        assert "text" in chunk, f"Chunk {i} missing text"
        
        successful_embeddings += 1
    
    print(f"[PASS] Successful embeddings: {successful_embeddings}")
    print(f"[PASS] Embedding dimension: {embedding_dimension}")
    
    # Verify all metadata preserved
    print("\n[PASS] All metadata preserved:")
    for chunk in result:
        print(f"  - Chunk {chunk['chunk_index']}: "
              f"doc_id={chunk['document_id']}, "
              f"page={chunk['page_number']}, "
              f"embedding_len={len(chunk['embedding'])}")
    
    # Test with empty text
    print("\n" + "=" * 60)
    print("TESTING EMPTY TEXT HANDLING")
    print("=" * 60)
    
    chunks_with_empty = [
        {
            "document_id": "doc2",
            "chunk_index": 0,
            "page_number": 1,
            "text": "Valid text"
        },
        {
            "document_id": "doc2",
            "chunk_index": 1,
            "page_number": 1,
            "text": ""
        },
        {
            "document_id": "doc2",
            "chunk_index": 2,
            "page_number": 1,
            "text": "Another valid text"
        }
    ]
    
    result_with_empty = generate_embeddings(chunks_with_empty)
    
    chunks_with_embeddings = sum(1 for c in result_with_empty if "embedding" in c)
    chunks_without_embeddings = sum(1 for c in result_with_empty if "embedding" not in c)
    
    print(f"\n[PASS] Chunks with embeddings: {chunks_with_embeddings}")
    print(f"[PASS] Chunks without embeddings (empty text): {chunks_without_embeddings}")
    
    assert chunks_with_embeddings == 2, "Should have 2 chunks with embeddings"
    assert chunks_without_embeddings == 1, "Should have 1 chunk without embedding"
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED [SUCCESS]")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_embeddings()
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
