"""
Manual test for retrieval service.
Run with: python -m apps.api.tests.test_retrieval_manual
"""

from app.ai.embeddings import generate_embeddings
from app.ai.vector_store import store_embeddings
from app.ai.retrieval import retrieve_chunks


def test_retrieval():
    """Test retrieval service with sample chunks."""
    
    print("\n" + "="*60)
    print("RETRIEVAL SERVICE TEST")
    print("="*60)
    
    # Step 1: Prepare sample chunks
    print("\n[1] Preparing sample chunks...")
    
    sample_chunks = [
        {
            "document_id": "test_doc_1",
            "chunk_index": 0,
            "page_number": 1,
            "text": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints."
        },
        {
            "document_id": "test_doc_1",
            "chunk_index": 1,
            "page_number": 1,
            "text": "FastAPI provides automatic API documentation, data validation, and high performance comparable to NodeJS and Go."
        },
        {
            "document_id": "test_doc_2",
            "chunk_index": 0,
            "page_number": 1,
            "text": "Python is a high-level programming language known for its simplicity and readability."
        },
        {
            "document_id": "test_doc_2",
            "chunk_index": 1,
            "page_number": 2,
            "text": "Machine learning and data science are popular applications of Python programming."
        },
        {
            "document_id": "test_doc_3",
            "chunk_index": 0,
            "page_number": 1,
            "text": "Web frameworks help developers build web applications more efficiently by providing reusable components."
        }
    ]
    
    print(f"Created {len(sample_chunks)} sample chunks")
    
    # Step 2: Generate embeddings
    print("\n[2] Generating embeddings...")
    chunks_with_embeddings = generate_embeddings(sample_chunks)
    print(f"Generated embeddings for {len(chunks_with_embeddings)} chunks")
    
    # Step 3: Store in vector database
    print("\n[3] Storing chunks in vector database...")
    store_embeddings(chunks_with_embeddings)
    print("Chunks stored successfully")
    
    # Step 4: Test query
    print("\n[4] Testing retrieval...")
    query = "What is FastAPI?"
    print(f"Query: '{query}'")
    
    # Step 5: Retrieve results
    print("\n[5] Retrieving results...")
    results = retrieve_chunks(query, top_k=2)
    
    # Step 6: Verify results
    print("\n[6] Verification:")
    print(f"Number of results: {len(results)}")
    
    if len(results) > 0:
        print("[OK] Results returned")
        
        # Check first result structure
        first_result = results[0]
        required_fields = ["text", "document_id", "chunk_index", "page_number", "score"]
        
        print("\nChecking result structure...")
        for field in required_fields:
            if field in first_result:
                print(f"[OK] Field '{field}' present")
            else:
                print(f"[FAIL] Field '{field}' missing")
        
        # Print top result preview
        print("\n" + "="*60)
        print("TOP RESULT PREVIEW")
        print("="*60)
        print(f"Document ID: {first_result['document_id']}")
        print(f"Chunk Index: {first_result['chunk_index']}")
        print(f"Page Number: {first_result['page_number']}")
        print(f"Score: {first_result['score']:.4f}")
        print(f"\nText Preview:")
        print(f"{first_result['text'][:150]}...")
        
        # Print all results summary
        print("\n" + "="*60)
        print("ALL RESULTS SUMMARY")
        print("="*60)
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"  Document: {result['document_id']}")
            print(f"  Chunk: {result['chunk_index']}")
            print(f"  Score: {result['score']:.4f}")
            print(f"  Text: {result['text'][:80]}...")
        
        print("\n" + "="*60)
        print("TEST PASSED [OK]")
        print("="*60)
    else:
        print("[FAIL] No results returned")
        print("\n" + "="*60)
        print("TEST FAILED [FAIL]")
        print("="*60)


if __name__ == "__main__":
    test_retrieval()

# Made with Bob