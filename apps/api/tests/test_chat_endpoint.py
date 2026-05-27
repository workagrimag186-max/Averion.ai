from fastapi.testclient import TestClient

from app.core.auth import RequestContext, get_request_context
from app.core.config import settings
from app.db.chat import ConversationNotFoundError, StoredChatMessages
from app.db.documents import DatabaseNotConfiguredError
from app.main import app


client = TestClient(app)


def test_chat_endpoint_returns_answer_and_stores_messages(monkeypatch) -> None:
    stored_payload = {}

    def fake_retrieve_chunks(query: str, top_k: int, organization_id: str) -> list[dict]:
        assert query == "What is the refund policy?"
        assert top_k > 0
        assert organization_id == settings.default_organization_id

        return [
            {
                "document_id": "doc_123",
                "chunk_index": 0,
                "chunk_id": "doc_123:0",
                "filename": "policy.pdf",
                "page_number": 4,
                "text": "Refunds are available within 30 days.",
                "score": 0.12
            }
        ]

    def fake_build_rag_prompt(question: str, chunks: list[dict]) -> str:
        assert question == "What is the refund policy?"
        assert chunks[0]["chunk_id"] == "doc_123:0"
        return "prompt"

    def fake_generate_answer(prompt: str, chunks: list[dict] | None = None) -> str:
        assert prompt == "prompt"
        return "Refunds are available within 30 days."

    def fake_store_chat_exchange(**kwargs) -> StoredChatMessages:
        stored_payload.update(kwargs)
        return StoredChatMessages(
            conversation_id="conv_123",
            user_message_id="msg_user_123",
            assistant_message_id="msg_assistant_123"
        )

    monkeypatch.setattr("app.api.chat.retrieve_chunks", fake_retrieve_chunks)
    monkeypatch.setattr("app.api.chat.build_rag_prompt", fake_build_rag_prompt)
    monkeypatch.setattr("app.api.chat.generate_answer", fake_generate_answer)
    monkeypatch.setattr("app.api.chat.store_chat_exchange", fake_store_chat_exchange)

    response = client.post(
        "/chat",
        json={
            "conversation_id": None,
            "question": "What is the refund policy?"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "conversation_id": "conv_123",
        "message_id": "msg_assistant_123",
        "answer": "Refunds are available within 30 days.",
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
        "sources": [
            {
                "document_id": "doc_123",
                "chunk_index": 0,
                "chunk_id": "doc_123:0",
                "filename": "policy.pdf",
                "page_number": 4,
                "text": "Refunds are available within 30 days.",
                "score": 0.12
            }
        ]
    }
    assert stored_payload["conversation_id"] is None
    assert stored_payload["organization_id"] == settings.default_organization_id
    assert stored_payload["user_id"] is None
    assert stored_payload["question"] == "What is the refund policy?"
    assert stored_payload["answer"] == "Refunds are available within 30 days."
    assert stored_payload["citations"][0]["chunk_id"] == "doc_123:0"


def test_chat_endpoint_handles_no_retrieval_results(monkeypatch) -> None:
    def fake_store_chat_exchange(**kwargs) -> StoredChatMessages:
        assert kwargs["citations"] == []
        return StoredChatMessages(
            conversation_id="conv_empty",
            user_message_id="msg_user_empty",
            assistant_message_id="msg_assistant_empty"
        )

    monkeypatch.setattr("app.api.chat.retrieve_chunks", lambda query, top_k, organization_id: [])
    monkeypatch.setattr(
        "app.api.chat.build_rag_prompt",
        lambda question, chunks: "prompt without context"
    )
    monkeypatch.setattr(
        "app.api.chat.generate_answer",
        lambda prompt, chunks=None: "I don't know based on the available documents."
    )
    monkeypatch.setattr("app.api.chat.store_chat_exchange", fake_store_chat_exchange)

    response = client.post(
        "/chat",
        json={
            "conversation_id": None,
            "question": "What does the handbook say about travel?"
        }
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == "conv_empty"
    assert response.json()["citations"] == []
    assert response.json()["answer"] == "I don't know based on the available documents."


def test_chat_endpoint_stores_authenticated_user_id(monkeypatch) -> None:
    stored_payload = {}

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000911",
            auth_user_id="00000000-0000-0000-0000-000000000912",
            email="teammate@example.com",
            role="member",
            is_authenticated=True
        )

    def fake_store_chat_exchange(**kwargs) -> StoredChatMessages:
        stored_payload.update(kwargs)
        return StoredChatMessages(
            conversation_id="conv_auth",
            user_message_id="msg_user_auth",
            assistant_message_id="msg_assistant_auth"
        )

    monkeypatch.setattr("app.api.chat.retrieve_chunks", lambda query, top_k, organization_id: [])
    monkeypatch.setattr("app.api.chat.build_rag_prompt", lambda question, chunks: "prompt")
    monkeypatch.setattr("app.api.chat.generate_answer", lambda prompt, chunks=None: "answer")
    monkeypatch.setattr("app.api.chat.store_chat_exchange", fake_store_chat_exchange)

    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.post(
            "/chat",
            json={
                "conversation_id": None,
                "question": "Hello?"
            }
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert stored_payload["organization_id"] == settings.default_organization_id
    assert stored_payload["user_id"] == "00000000-0000-0000-0000-000000000911"


def test_chat_endpoint_returns_500_for_llm_provider_error(monkeypatch) -> None:
    monkeypatch.setattr("app.api.chat.retrieve_chunks", lambda query, top_k, organization_id: [])
    monkeypatch.setattr("app.api.chat.build_rag_prompt", lambda question, chunks: "prompt")

    def fake_generate_answer(prompt: str, chunks: list[dict] | None = None) -> str:
        raise ValueError("Unsupported LLM provider: bad-provider")

    monkeypatch.setattr("app.api.chat.generate_answer", fake_generate_answer)

    response = client.post(
        "/chat",
        json={
            "conversation_id": None,
            "question": "Hello?"
        }
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Unsupported LLM provider: bad-provider"}


def test_chat_endpoint_returns_503_when_database_is_not_configured(monkeypatch) -> None:
    monkeypatch.setattr("app.api.chat.retrieve_chunks", lambda query, top_k, organization_id: [])
    monkeypatch.setattr("app.api.chat.build_rag_prompt", lambda question, chunks: "prompt")
    monkeypatch.setattr("app.api.chat.generate_answer", lambda prompt, chunks=None: "answer")

    def fake_store_chat_exchange(**kwargs) -> StoredChatMessages:
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    monkeypatch.setattr("app.api.chat.store_chat_exchange", fake_store_chat_exchange)

    response = client.post(
        "/chat",
        json={
            "conversation_id": None,
            "question": "Hello?"
        }
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "DATABASE_URL is not configured."}


def test_chat_endpoint_returns_404_for_cross_organization_conversation(monkeypatch) -> None:
    monkeypatch.setattr("app.api.chat.retrieve_chunks", lambda query, top_k, organization_id: [])
    monkeypatch.setattr("app.api.chat.build_rag_prompt", lambda question, chunks: "prompt")
    monkeypatch.setattr("app.api.chat.generate_answer", lambda prompt, chunks=None: "answer")

    def fake_store_chat_exchange(**kwargs) -> StoredChatMessages:
        raise ConversationNotFoundError("Conversation not found for this organization.")

    monkeypatch.setattr("app.api.chat.store_chat_exchange", fake_store_chat_exchange)

    response = client.post(
        "/chat",
        json={
            "conversation_id": "00000000-0000-0000-0000-000000000999",
            "question": "Hello?"
        }
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found for this organization."}
