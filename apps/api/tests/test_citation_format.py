"""
Test that citations use user-friendly format instead of raw UUIDs.
"""

from app.ai.prompt_builder import build_rag_prompt


def test_prompt_uses_numbered_citations():
    """Test that prompt uses [Source N] format instead of raw chunk IDs"""
    chunks = [
        {
            "document_id": "9dc05cb4-7112-47d2-a586-0201e4fe68d5",
            "chunk_index": 0,
            "chunk_id": "9dc05cb4-7112-47d2-a586-0201e4fe68d5:0",
            "text": "The system manages drone shows."
        },
        {
            "document_id": "9dc05cb4-7112-47d2-a586-0201e4fe68d5",
            "chunk_index": 1,
            "chunk_id": "9dc05cb4-7112-47d2-a586-0201e4fe68d5:1",
            "text": "It supports multiple drones simultaneously."
        }
    ]
    
    prompt = build_rag_prompt("What does the system do?", chunks)
    
    # Should contain user-friendly citations
    assert "[Source 1]" in prompt
    assert "[Source 2]" in prompt
    
    # Should NOT contain raw UUIDs
    assert "9dc05cb4-7112-47d2-a586-0201e4fe68d5:0" not in prompt
    assert "9dc05cb4-7112-47d2-a586-0201e4fe68d5:1" not in prompt
    
    # Should instruct to use numbered citations
    assert "source numbers" in prompt.lower() or "numbered citations" in prompt.lower()


def test_prompt_instructs_numbered_citation_usage():
    """Test that prompt explicitly tells LLM to use numbered citations"""
    chunks = [
        {
            "document_id": "doc1",
            "chunk_index": 0,
            "chunk_id": "doc1:0",
            "text": "Sample text"
        }
    ]
    
    prompt = build_rag_prompt("Test question?", chunks)
    
    # Should contain instructions about using numbered citations
    assert "[1]" in prompt or "[Source 1]" in prompt
    assert "NOT the internal IDs" in prompt or "numbered citations" in prompt.lower()


# Made with Bob