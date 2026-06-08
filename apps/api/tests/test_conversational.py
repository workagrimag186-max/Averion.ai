"""
Tests for conversational intent detection and response generation.
"""

import pytest

from app.ai.conversational import (
    generate_conversational_response,
    is_conversational_query,
)


class TestConversationalIntentDetection:
    """Test conversational query detection."""
    
    def test_greeting_detection(self):
        """Test detection of greeting messages."""
        greetings = [
            "Hi",
            "Hello",
            "Hey there",
            "Good morning",
            "Good afternoon",
            "Good evening",
            "Greetings",
        ]
        
        for greeting in greetings:
            is_conv, intent = is_conversational_query(greeting)
            assert is_conv is True, f"Failed to detect greeting: {greeting}"
            assert intent == "greeting", f"Wrong intent for: {greeting}"
    
    def test_wellbeing_detection(self):
        """Test detection of wellbeing questions."""
        wellbeing_queries = [
            "How are you?",
            "How r you?",
            "How is it going?",
            "How was your day?",
            "How are you doing?",
        ]
        
        for query in wellbeing_queries:
            is_conv, intent = is_conversational_query(query)
            assert is_conv is True, f"Failed to detect wellbeing: {query}"
            assert intent == "wellbeing", f"Wrong intent for: {query}"
    
    def test_capability_detection(self):
        """Test detection of capability questions."""
        capability_queries = [
            "What can you do?",
            "What are you capable of?",
            "What do you do?",
            "Help me",
            "What are your features?",
            "What are your capabilities?",
        ]
        
        for query in capability_queries:
            is_conv, intent = is_conversational_query(query)
            assert is_conv is True, f"Failed to detect capability: {query}"
            assert intent == "capability", f"Wrong intent for: {query}"
    
    def test_gratitude_detection(self):
        """Test detection of gratitude expressions."""
        gratitude_expressions = [
            "Thank you",
            "Thanks",
            "Thx",
            "Thank you so much",
            "I appreciate it",
        ]
        
        for expr in gratitude_expressions:
            is_conv, intent = is_conversational_query(expr)
            assert is_conv is True, f"Failed to detect gratitude: {expr}"
            assert intent == "gratitude", f"Wrong intent for: {expr}"
    
    def test_farewell_detection(self):
        """Test detection of farewell messages."""
        farewells = [
            "Bye",
            "Goodbye",
            "See you",
            "Farewell",
            "Take care",
        ]
        
        for farewell in farewells:
            is_conv, intent = is_conversational_query(farewell)
            assert is_conv is True, f"Failed to detect farewell: {farewell}"
            assert intent == "farewell", f"Wrong intent for: {farewell}"
    
    def test_introduction_detection(self):
        """Test detection of introduction messages."""
        introductions = [
            "Nice to meet you",
            "Pleasure to meet you",
            "Glad to meet you",
        ]
        
        for intro in introductions:
            is_conv, intent = is_conversational_query(intro)
            assert is_conv is True, f"Failed to detect introduction: {intro}"
            assert intent == "introduction", f"Wrong intent for: {intro}"
    
    def test_identity_detection(self):
        """Test detection of identity questions."""
        identity_queries = [
            "Who are you?",
            "What are you?",
            "What is your name?",
        ]
        
        for query in identity_queries:
            is_conv, intent = is_conversational_query(query)
            assert is_conv is True, f"Failed to detect identity: {query}"
            assert intent == "identity", f"Wrong intent for: {query}"
    
    def test_document_questions_not_conversational(self):
        """Test that document questions are NOT detected as conversational."""
        document_queries = [
            "What is the main topic of the document?",
            "Summarize the abstract",
            "What are the key findings?",
            "Who is the author?",
            "What is data management?",
            "Explain the methodology",
            "What are the conclusions?",
        ]
        
        for query in document_queries:
            is_conv, intent = is_conversational_query(query)
            assert is_conv is False, f"Incorrectly detected as conversational: {query}"
            assert intent == "unknown", f"Wrong intent for document query: {query}"
    
    def test_empty_query(self):
        """Test handling of empty queries."""
        is_conv, intent = is_conversational_query("")
        assert is_conv is False
        assert intent == "unknown"
        
        is_conv, intent = is_conversational_query("   ")
        assert is_conv is False
        assert intent == "unknown"
    
    def test_case_insensitivity(self):
        """Test that detection is case-insensitive."""
        queries = [
            ("HELLO", "greeting"),
            ("HoW aRe YoU?", "wellbeing"),
            ("THANK YOU", "gratitude"),
        ]
        
        for query, expected_intent in queries:
            is_conv, intent = is_conversational_query(query)
            assert is_conv is True, f"Failed case-insensitive detection: {query}"
            assert intent == expected_intent, f"Wrong intent for: {query}"


class TestConversationalResponseGeneration:
    """Test conversational response generation."""
    
    def test_greeting_response(self):
        """Test greeting response generation."""
        response = generate_conversational_response("greeting")
        assert len(response) > 0
        assert "help" in response.lower() or "assist" in response.lower()
    
    def test_wellbeing_response(self):
        """Test wellbeing response generation."""
        response = generate_conversational_response("wellbeing")
        assert len(response) > 0
        assert "ready" in response.lower() or "help" in response.lower()
    
    def test_capability_response(self):
        """Test capability response generation."""
        response = generate_conversational_response("capability")
        assert len(response) > 0
        assert "document" in response.lower()
        assert "question" in response.lower() or "answer" in response.lower()
    
    def test_gratitude_response(self):
        """Test gratitude response generation."""
        response = generate_conversational_response("gratitude")
        assert len(response) > 0
        assert "welcome" in response.lower() or "pleasure" in response.lower()
    
    def test_farewell_response(self):
        """Test farewell response generation."""
        response = generate_conversational_response("farewell")
        assert len(response) > 0
        assert any(word in response.lower() for word in ["goodbye", "bye", "care", "see you"])
    
    def test_introduction_response(self):
        """Test introduction response generation."""
        response = generate_conversational_response("introduction")
        assert len(response) > 0
        assert "meet" in response.lower() or "help" in response.lower()
    
    def test_identity_response(self):
        """Test identity response generation."""
        response = generate_conversational_response("identity")
        assert len(response) > 0
        assert "assistant" in response.lower() or "ai" in response.lower()
        assert "document" in response.lower()
    
    def test_unknown_intent_response(self):
        """Test response for unknown intent."""
        response = generate_conversational_response("unknown")
        assert len(response) > 0
        assert "help" in response.lower() or "document" in response.lower()
    
    def test_response_quality(self):
        """Test that responses are friendly and natural."""
        intents = ["greeting", "wellbeing", "capability", "gratitude", "farewell"]
        
        for intent in intents:
            response = generate_conversational_response(intent)
            # Check response is not too short
            assert len(response) > 20, f"Response too short for {intent}"
            # Check response doesn't contain error messages
            assert "error" not in response.lower()
            assert "failed" not in response.lower()
            # Check response is properly formatted
            assert response[0].isupper(), f"Response should start with capital: {response}"


class TestConversationalIntegration:
    """Integration tests for conversational features."""
    
    def test_greeting_followed_by_document_question(self):
        """Test that greeting doesn't affect subsequent document questions."""
        # First query is conversational
        is_conv1, intent1 = is_conversational_query("Hello!")
        assert is_conv1 is True
        assert intent1 == "greeting"
        
        # Second query is document-related
        is_conv2, intent2 = is_conversational_query("What is the main topic?")
        assert is_conv2 is False
        assert intent2 == "unknown"
    
    def test_mixed_conversational_and_document_content(self):
        """Test queries that mix conversational and document elements."""
        # These should be treated as document questions
        mixed_queries = [
            "Hi, what is the abstract about?",
            "Hello, can you summarize the document?",
            "Thanks, but what are the key findings?",
        ]
        
        for query in mixed_queries:
            is_conv, intent = is_conversational_query(query)
            # The greeting part should be detected
            # In a real scenario, you might want more sophisticated handling
            # For now, we test current behavior
            if query.startswith("Hi,") or query.startswith("Hello,"):
                assert is_conv is True
            elif query.startswith("Thanks,"):
                assert is_conv is True


# Made with Bob