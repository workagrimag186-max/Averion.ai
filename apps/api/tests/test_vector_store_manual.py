import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ai.vector_store import store_embeddings, search_similar


def test_vector_store():
    """
    Manual test for vector store functionality.
    Tests storing embeddings and similarity search.
    """
    print("=" * 60)
    print("VECTOR STORE TEST")
    print("=" * 60)
    
    # Create sample chunks with mock embeddings (384 dimensions for all-MiniLM-L6-v2)
    sample_chunks = [
        {
            "document_id": "doc_001",
            "chunk_index": 0,
            "page_number": 1,
            "text": "Machine learning is a subset of artificial intelligence.",
            "embedding": [0.1] * 384  # Mock embedding
        },
        {
            "document_id": "doc_001",
            "chunk_index": 1,
            "page_number": 1,
            "text": "Deep learning uses neural networks with multiple layers.",
            "embedding": [0.2] * 384  # Mock embedding
        },
        {
            "document_id": "doc_001",
            "chunk_index": 2,
            "page_number": 2,
            "text": "Natural language processing enables computers to understand human language.",
            "embedding": [0.3] * 384  # Mock embedding
        },
        {
            "document_id": "doc_002",
            "chunk_index": 0,
            "page_number": 1,
            "text": "Python is a popular programming language for data science.",
            "embedding": [0.4] * 384  # Mock embedding
        },
        {
            "document_id": "doc_002",
            "chunk_index": 1,
            "page_number": 1,
            "text": "FastAPI is a modern web framework for building APIs with Python.",
            "embedding": [0.5] * 384  # Mock embedding
        }
    ]
    
    print(f"\n1. STORING EMBEDDINGS")
    print("-" * 60)
    print(f"Number of chunks to store: {len(sample_chunks)}")
    
    # Store embeddings
    store_embeddings(sample_chunks)
    print("[OK] Embeddings stored successfully")
    
    print(f"\n2. SIMILARITY SEARCH")
    print("-" * 60)
    
    # Create a query embedding (similar to first chunk)
    query_embedding = [0.15] * 384  # Should be closest to first chunk
    print(f"Query embedding dimension: {len(query_embedding)}")
    
    # Search for similar chunks
    results = search_similar(query_embedding, top_k=3)
    
    print(f"\nNumber of results returned: {len(results)}")
    
    if results:
        print("\n3. SEARCH RESULTS")
        print("-" * 60)
        
        for idx, result in enumerate(results, 1):
            print(f"\nResult #{idx}:")
            print(f"  Text: {result['text'][:80]}...")
            print(f"  Document ID: {result['metadata']['document_id']}")
            print(f"  Chunk Index: {result['metadata']['chunk_index']}")
            print(f"  Page Number: {result['metadata']['page_number']}")
            print(f"  Distance Score: {result['score']:.4f}")
        
        print("\n4. TOP RESULT PREVIEW")
        print("-" * 60)
        top_result = results[0]
        print(f"Text: {top_result['text']}")
        print(f"Metadata: {top_result['metadata']}")
        print(f"Score: {top_result['score']:.4f}")
        
        print("\n" + "=" * 60)
        print("[OK] TEST PASSED")
        print("=" * 60)
    else:
        print("\n[FAIL] TEST FAILED: No results returned")
        print("=" * 60)


if __name__ == "__main__":
    test_vector_store()

# Made with Bob
