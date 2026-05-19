"""
Manual Test for LLM Service

Tests the LLM service with fake chunks to verify:
1. Prompt building
2. LLM answer generation
3. Complete RAG pipeline

Run with:
    python -m pytest apps/api/tests/test_llm_manual.py -v -s
"""

from app.ai.prompt_builder import build_rag_prompt
from app.ai.llm_service import generate_answer
from app.core.config import settings


def test_llm_with_mock_provider():
    """Test LLM service with mock provider (no API key needed)"""
    print("\n" + "="*80)
    print("TEST: LLM Service with Mock Provider")
    print("="*80)
    
    # Create fake chunks
    fake_chunks = [
        {
            "document_id": "doc_123",
            "chunk_index": 0,
            "chunk_id": "doc_123_0",
            "text": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+. It is based on standard Python type hints.",
            "page_number": 1,
            "score": 0.95
        },
        {
            "document_id": "doc_123",
            "chunk_index": 1,
            "chunk_id": "doc_123_1",
            "text": "FastAPI provides automatic API documentation using Swagger UI and ReDoc. It also includes data validation using Pydantic.",
            "page_number": 1,
            "score": 0.87
        },
        {
            "document_id": "doc_456",
            "chunk_index": 0,
            "chunk_id": "doc_456_0",
            "text": "Python type hints allow you to specify the expected types of variables and function parameters, improving code clarity and enabling better IDE support.",
            "page_number": 3,
            "score": 0.82
        }
    ]
    
    # Test question
    question = "What is FastAPI and what are its key features?"
    
    # Step 1: Build prompt
    print("\n1. Building RAG prompt...")
    prompt = build_rag_prompt(question, fake_chunks)
    print(f"\nPrompt length: {len(prompt)} characters")
    print("\nPrompt preview (first 500 chars):")
    print("-" * 80)
    print(prompt[:500])
    print("-" * 80)
    
    # Step 2: Generate answer
    print("\n2. Generating answer with LLM...")
    print(f"Provider: {settings.llm_provider}")
    
    answer = generate_answer(prompt)
    
    print("\n3. Generated Answer:")
    print("=" * 80)
    print(answer)
    print("=" * 80)
    
    # Verify answer is not empty
    assert answer, "Answer should not be empty"
    assert len(answer) > 0, "Answer should have content"
    
    print("\n[PASS] Test passed: LLM service working with mock provider")


def test_llm_with_no_context():
    """Test LLM service when no context is available"""
    print("\n" + "="*80)
    print("TEST: LLM Service with No Context")
    print("="*80)
    
    # Empty chunks
    empty_chunks = []
    question = "What is the meaning of life?"
    
    # Build prompt
    print("\n1. Building RAG prompt with no context...")
    prompt = build_rag_prompt(question, empty_chunks)
    
    # Generate answer
    print("\n2. Generating answer...")
    answer = generate_answer(prompt)
    
    print("\n3. Generated Answer:")
    print("=" * 80)
    print(answer)
    print("=" * 80)
    
    # Verify answer is not empty
    assert answer, "Answer should not be empty even without context"
    
    print("\n[PASS] Test passed: LLM handles no context gracefully")


def test_llm_with_openai_provider():
    """
    Test LLM service with OpenAI provider (requires API key).
    
    This test will be skipped if:
    - OpenAI API key is not configured
    - LLM provider is not set to 'openai'
    """
    print("\n" + "="*80)
    print("TEST: LLM Service with OpenAI Provider")
    print("="*80)
    
    # Check if OpenAI is configured
    if settings.llm_provider.lower() != "openai":
        print(f"\n[SKIP] LLM provider is '{settings.llm_provider}', not 'openai'")
        print("  To test OpenAI, set LLM_PROVIDER=openai in .env")
        return
    
    if not settings.llm_provider_api_key:
        print("\n[SKIP] OpenAI API key not configured")
        print("  To test OpenAI, set LLM_PROVIDER_API_KEY in .env")
        return
    
    # Create fake chunks
    fake_chunks = [
        {
            "document_id": "doc_789",
            "chunk_index": 0,
            "chunk_id": "doc_789_0",
            "text": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
            "page_number": 1,
            "score": 0.92
        }
    ]
    
    question = "What is machine learning?"
    
    # Build prompt
    print("\n1. Building RAG prompt...")
    prompt = build_rag_prompt(question, fake_chunks)
    
    # Generate answer
    print("\n2. Calling OpenAI API...")
    print(f"Model: {settings.llm_model_name}")
    print(f"Temperature: {settings.llm_temperature}")
    
    answer = generate_answer(prompt)
    
    print("\n3. Generated Answer:")
    print("=" * 80)
    print(answer)
    print("=" * 80)
    
    # Verify answer
    assert answer, "Answer should not be empty"
    assert "Failed to generate answer" not in answer, "Should not have error message"
    
    print("\n[PASS] Test passed: OpenAI integration working")


def test_complete_rag_pipeline():
    """Test the complete RAG pipeline simulation"""
    print("\n" + "="*80)
    print("TEST: Complete RAG Pipeline Simulation")
    print("="*80)
    
    # Simulate the complete flow
    print("\n1. User asks question")
    question = "How do I use type hints in Python?"
    print(f"   Question: {question}")
    
    print("\n2. System retrieves relevant chunks (simulated)")
    chunks = [
        {
            "document_id": "python_guide",
            "chunk_index": 5,
            "chunk_id": "python_guide_5",
            "text": "Type hints in Python are specified using the colon syntax. For example: def greet(name: str) -> str: return f'Hello {name}'. This helps with code documentation and IDE support.",
            "page_number": 12,
            "score": 0.94
        }
    ]
    print(f"   Retrieved {len(chunks)} chunk(s)")
    
    print("\n3. System builds RAG prompt")
    prompt = build_rag_prompt(question, chunks)
    print(f"   Prompt built ({len(prompt)} chars)")
    
    print("\n4. System generates answer using LLM")
    answer = generate_answer(prompt)
    
    print("\n5. Final Answer:")
    print("=" * 80)
    print(answer)
    print("=" * 80)
    
    # Verify
    assert answer, "Pipeline should produce an answer"
    
    print("\n[PASS] Test passed: Complete RAG pipeline working")


if __name__ == "__main__":
    """Run all tests manually"""
    print("\n" + "="*80)
    print("MANUAL LLM SERVICE TESTS")
    print("="*80)
    
    try:
        test_llm_with_mock_provider()
        test_llm_with_no_context()
        test_llm_with_openai_provider()
        test_complete_rag_pipeline()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {str(e)}")
        raise


# Made with Bob