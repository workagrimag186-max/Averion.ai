"""
LLM Service

Provider-agnostic interface for generating answers using LLM providers.
Supports OpenAI, Groq, and mock provider for testing.
"""

from app.core.config import settings


def generate_answer(prompt: str, chunks: list[dict] | None = None) -> str:
    """
    Generate an answer using the configured LLM provider.
    
    Args:
        prompt: The complete prompt string (already built using RAG prompt builder)
        chunks: Retrieved chunks for context (used by mock provider)
        
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
    elif provider == "groq":
        return _call_groq(prompt)
    elif provider == "mock":
        return _call_mock(prompt, chunks or [])
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
            print("[ERROR] OpenAI API key is not configured")
            return "Failed to generate answer. OpenAI API key is not configured."
        
        print(f"[DEBUG] Using OpenAI model: {settings.llm_model_name}")
        print(f"[DEBUG] API key present: {len(settings.llm_provider_api_key)} chars")
        
        # Import OpenAI client
        try:
            from openai import OpenAI
        except ImportError as e:
            print(f"[ERROR] OpenAI library import failed: {e}")
            return "Failed to generate answer. OpenAI library is not installed. Run: pip install openai"
        
        # Initialize client
        client = OpenAI(api_key=settings.llm_provider_api_key)
        
        print("[DEBUG] Calling OpenAI API...")
        
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
            print("[ERROR] OpenAI returned empty response")
            return "Failed to generate answer. Please try again."
        
        print(f"[DEBUG] OpenAI response received: {len(answer)} chars")
        return answer.strip()
        
    except Exception as e:
        # Log detailed error
        error_msg = str(e)
        print(f"[ERROR] OpenAI API error: {error_msg}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        
        # Return user-friendly message with hint
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return f"Failed to generate answer. API key error: {error_msg}. Please check your OpenAI API key."
        elif "rate_limit" in error_msg.lower():
            return "Failed to generate answer. Rate limit exceeded. Please try again in a moment."
        elif "model" in error_msg.lower():
            return f"Failed to generate answer. Model error: {error_msg}. Check LLM_MODEL_NAME in .env"
        else:
            return f"Failed to generate answer: {error_msg}"


def _call_groq(prompt: str) -> str:
    """
    Call Groq API to generate an answer.
    
    Args:
        prompt: The complete prompt string
        
    Returns:
        Answer from Groq
    """
    try:
        # Check for API key
        if not settings.llm_provider_api_key:
            print("[ERROR] Groq API key is not configured")
            return "Failed to generate answer. Groq API key is not configured."
        
        # Use a currently supported Groq model
        # Options: llama-3.3-70b-versatile, llama-3.1-70b-versatile, mixtral-8x7b-32768
        groq_model = "llama-3.3-70b-versatile"
        
        print(f"[DEBUG] Using Groq model: {groq_model}")
        print(f"[DEBUG] API key present: {len(settings.llm_provider_api_key)} chars")
        
        # Import OpenAI client
        try:
            from openai import OpenAI
        except ImportError as e:
            print(f"[ERROR] OpenAI library import failed: {e}")
            return "Failed to generate answer. OpenAI library is not installed. Run: pip install openai"
        
        # Initialize client with Groq base URL
        client = OpenAI(
            api_key=settings.llm_provider_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        print("[DEBUG] Calling Groq API...")
        
        # Call chat completion API
        response = client.chat.completions.create(
            model=groq_model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        # Extract answer
        answer = response.choices[0].message.content
        
        if not answer:
            print("[ERROR] Groq returned empty response")
            return "Failed to generate answer. Please try again."
        
        print(f"[DEBUG] Groq response received: {len(answer)} chars")
        return answer.strip()
        
    except Exception as e:
        # Log detailed error
        error_msg = str(e)
        print(f"[ERROR] Groq API error: {error_msg}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        
        # Return user-friendly message with hint
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return f"Failed to generate answer. API key error: {error_msg}. Please check your Groq API key."
        elif "rate_limit" in error_msg.lower():
            return "Failed to generate answer. Rate limit exceeded. Please try again in a moment."
        elif "model" in error_msg.lower():
            return f"Failed to generate answer. Model error: {error_msg}. The model 'llama3-8b-8192' may not be available."
        else:
            return f"Failed to generate answer: {error_msg}"


def _call_mock(prompt: str, chunks: list[dict]) -> str:
    """
    Mock provider for testing without API calls.
    
    NOTE: This is a VERY LIMITED mock. For production use, set LLM_PROVIDER=openai
    Mock cannot truly understand context, summarize, or reason about content.
    
    Args:
        prompt: The complete prompt string
        chunks: Retrieved chunks for context
        
    Returns:
        Mock answer based on the prompt and context
    """
    # Extract question from prompt
    lines = prompt.split("\n")
    question = ""
    
    for i, line in enumerate(lines):
        if line.strip() == "Question:":
            if i + 1 < len(lines):
                question = lines[i + 1].strip()
                break
    
    if not chunks:
        return f"I don't have enough information to answer '{question}'. Please upload relevant documents first."
    
    # Get ALL text from ALL chunks
    all_text = " ".join([chunk.get("text", "").strip() for chunk in chunks])
    
    # Split into sentences
    sentences = [s.strip() for s in all_text.split(".") if s.strip()]
    
    question_lower = question.lower()
    
    # Extract key terms from question (ignore common words)
    ignore_words = {"what", "is", "are", "the", "of", "in", "a", "an", "how", "why",
                    "when", "where", "who", "which", "with", "for", "to", "from", "about",
                    "context", "content", "file", "document", "resume"}
    
    key_terms = []
    for word in question_lower.split():
        clean = word.strip("?.,!;:()")
        if clean and clean not in ignore_words and len(clean) > 2:
            key_terms.append(clean)
    
    # Score sentences by keyword relevance
    scored_sentences = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        score = sum(1 for term in key_terms if term in sentence_lower)
        if score > 0:
            scored_sentences.append((score, sentence))
    
    # Sort by score (most relevant first)
    scored_sentences.sort(reverse=True, key=lambda x: x[0])
    
    # Get top relevant sentences
    if scored_sentences:
        relevant = [s[1] for s in scored_sentences[:8]]  # Top 8 sentences
    else:
        relevant = sentences[:8]  # Fallback to first 8
    
    # Special handling for specific question types
    if "abstract" in question_lower:
        # Look for abstract section
        abstract_sentences = []
        for i, sentence in enumerate(sentences):
            if "abstract" in sentence.lower() or i < 5:  # First 5 or contains "abstract"
                abstract_sentences.append(sentence)
                if len(abstract_sentences) >= 6:
                    break
        if abstract_sentences:
            return f"Abstract: {'. '.join(abstract_sentences)}."
        return f"Based on the document: {'. '.join(relevant[:6])}."
    
    elif "conclusion" in question_lower:
        # Look for conclusion section
        conclusion_sentences = []
        for sentence in sentences:
            if any(word in sentence.lower() for word in ["conclusion", "conclude", "summary", "finally", "result"]):
                conclusion_sentences.append(sentence)
        if conclusion_sentences:
            return f"Conclusion: {'. '.join(conclusion_sentences[:6])}."
        # If no conclusion found, use last sentences
        return f"Based on the document: {'. '.join(sentences[-6:])}."
    
    elif "resume" in question_lower or "cv" in question_lower:
        # For resume questions, provide comprehensive overview
        return f"This appears to be a resume/CV. Key information: {'. '.join(relevant[:10])}. [Note: For better understanding, please use OpenAI provider by setting LLM_PROVIDER=openai in .env]"
    
    elif "who" in question_lower:
        # Person-related question
        return f"Based on the document: {'. '.join(relevant[:6])}."
    
    elif "what" in question_lower:
        return f"According to the document: {'. '.join(relevant[:6])}."
    
    elif "how" in question_lower:
        return f"The document explains: {'. '.join(relevant[:6])}."
    
    else:
        # Generic response with most relevant content
        return f"Based on the retrieved context: {'. '.join(relevant[:8])}. [Note: Mock LLM has limited understanding. For accurate answers, use OpenAI by setting LLM_PROVIDER=openai in .env]"


# Made with Bob