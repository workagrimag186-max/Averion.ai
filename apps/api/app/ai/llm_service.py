"""
LLM Service

Provider-agnostic interface for generating answers using LLM providers.
Supports OpenAI and mock provider for testing.
"""

from app.core.config import settings


def generate_answer(prompt: str) -> str:
    """
    Generate an answer using the configured LLM provider.
    
    Args:
        prompt: The complete prompt string (already built using RAG prompt builder)
        
    Returns:
        Final answer string from the LLM
        
    Raises:
        ValueError: If the LLM provider is not supported
        
    Security:
        - ONLY passes the generated prompt to the LLM
        - Does NOT pass database_url, raw database records, or internal config
    """
    # Validate input
    if not prompt or not prompt.strip():
        return "I cannot provide an answer without a valid question."
    
    # Route to appropriate provider
    provider = settings.llm_provider.lower()
    
    if provider == "openai":
        return _call_openai(prompt)
    elif provider == "mock":
        return _call_mock(prompt)
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


def _call_openai(prompt: str) -> str:
    """
    Call OpenAI API to generate an answer.
    
    Args:
        prompt: The complete prompt string
        
    Returns:
        Answer from OpenAI
    """
    try:
        # Check for API key
        if not settings.llm_provider_api_key:
            return "Failed to generate answer. OpenAI API key is not configured."
        
        # Import OpenAI client
        try:
            from openai import OpenAI
        except ImportError:
            return "Failed to generate answer. OpenAI library is not installed."
        
        # Initialize client
        client = OpenAI(api_key=settings.llm_provider_api_key)
        
        # Call chat completion API
        response = client.chat.completions.create(
            model=settings.llm_model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        
        # Extract answer
        answer = response.choices[0].message.content
        
        if not answer:
            return "Failed to generate answer. Please try again."
        
        return answer.strip()
        
    except Exception as e:
        # Log error in production, return safe message to user
        print(f"OpenAI API error: {str(e)}")
        return "Failed to generate answer. Please try again."


def _call_mock(prompt: str) -> str:
    """
    Mock provider for testing without API calls.
    
    Args:
        prompt: The complete prompt string
        
    Returns:
        Mock answer based on the prompt
    """
    # Extract question from prompt
    lines = prompt.split("\n")
    question_line = ""
    
    for i, line in enumerate(lines):
        if line.strip() == "Question:":
            if i + 1 < len(lines):
                question_line = lines[i + 1].strip()
                break
    
    # Generate mock response
    if not question_line:
        return "Mock response: I received your prompt but couldn't extract the question."
    
    # Check if context was provided
    has_context = "Context:" in prompt and "No relevant context provided." not in prompt
    
    if has_context:
        return f"Mock response: Based on the provided context, I can answer your question about '{question_line}'. This is a simulated answer for testing purposes."
    else:
        return f"Mock response: I don't have enough context to answer '{question_line}'. This is a simulated answer for testing purposes."


# Made with Bob