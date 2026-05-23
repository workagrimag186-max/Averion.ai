import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatCitation, ChatRequest, ChatResponse


def test_chat_request_accepts_new_conversation_question() -> None:
    request = ChatRequest(question="What is the refund policy?")

    assert request.conversation_id is None
    assert request.question == "What is the refund policy?"


def test_chat_request_accepts_existing_conversation_id() -> None:
    request = ChatRequest(
        conversation_id="7f1d5d0a-6fd1-4ff2-a95f-8c84a32b7f83",
        question="Can you explain that again?"
    )

    assert request.conversation_id == "7f1d5d0a-6fd1-4ff2-a95f-8c84a32b7f83"
    assert request.question == "Can you explain that again?"


def test_chat_request_rejects_empty_question() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(question="")


def test_chat_response_serializes_citation_contract() -> None:
    response = ChatResponse(
        conversation_id="conv_123",
        message_id="msg_456",
        answer="Refund requests are allowed within 30 days.",
        citations=[
            ChatCitation(
                document_id="doc_123",
                chunk_index=0,
                chunk_id="doc_123:0",
                filename="policy.pdf",
                page_number=4,
                snippet="Refunds are available within 30 days.",
                score=0.12
            )
        ],
        sources=[]
    )

    assert response.model_dump() == {
        "conversation_id": "conv_123",
        "message_id": "msg_456",
        "answer": "Refund requests are allowed within 30 days.",
        "citations": [
            {
                "document_id": "doc_123",
                "chunk_index": 0,
                "chunk_id": "doc_123:0",
                "filename": "policy.pdf",
                "page_number": 4,
                "snippet": "Refunds are available within 30 days.",
                "score": 0.12
            }
        ],
        "sources": []
    }
