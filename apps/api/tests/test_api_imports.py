"""
Quick test to verify API imports work correctly
"""

def test_api_imports():
    """Test that all API modules can be imported"""
    from app.main import app
    from app.api.chat import router as chat_router
    from app.ai.llm_service import generate_answer
    
    print("[PASS] All imports successful")
    print(f"[PASS] App created: {app.title}")
    print(f"[PASS] Chat router available: {chat_router.prefix}")
    
    assert app is not None
    assert chat_router is not None
    assert generate_answer is not None

# Made with Bob
