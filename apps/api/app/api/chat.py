"""
Chat API Endpoint

Handles chat requests by:
1. Retrieving relevant document chunks
2. Building RAG prompt
3. Generating answer using LLM
"""

import uuid
from fastapi import APIRouter, HTTPException

from app.ai.retrieval import retrieve_chunks
from app.ai.prompt_builder import build_rag_prompt
from app.ai.llm_service import generate_answer
from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse, ChatCitation

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a chat question and return an AI-generated answer with citations.
    
    Flow:
    1. Retrieve relevant document chunks using vector search
    2. Build RAG prompt with retrieved context
    3. Generate answer using configured LLM provider
    4. Return answer with source citations
    
    Args:
        request: ChatRequest containing the user's question
        
    Returns:
        ChatResponse with answer and citations
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        # Validate question
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Step 1: Retrieve relevant chunks
        chunks = retrieve_chunks(
            query=request.question,
            top_k=settings.retrieval_top_k
        )
        
        # Step 2: Build RAG prompt
        prompt = build_rag_prompt(
            question=request.question,
            chunks=chunks
        )
        
        # Step 3: Generate answer using LLM
        # SECURITY: Only the prompt is passed to the LLM
        # No database_url, raw records, or internal config is exposed
        answer = generate_answer(prompt)
        
        # Step 4: Build citations from retrieved chunks
        citations = []
        for chunk in chunks:
            citation = ChatCitation(
                document_id=chunk.get("document_id", "unknown"),
                chunk_index=chunk.get("chunk_index", 0),
                chunk_id=chunk.get("chunk_id", "unknown"),
                filename=chunk.get("document_id", "unknown"),  # TODO: Get actual filename from DB
                page_number=chunk.get("page_number"),
                snippet=chunk.get("text", "")[:200],  # First 200 chars as snippet
                score=chunk.get("score")
            )
            citations.append(citation)
        
        # Generate IDs
        conversation_id = request.conversation_id or str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        
        return ChatResponse(
            conversation_id=conversation_id,
            message_id=message_id,
            answer=answer,
            citations=citations
        )
        
    except ValueError as e:
        # Handle LLM provider errors
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # Log error in production
        print(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process chat request. Please try again."
        )


# Made with Bob