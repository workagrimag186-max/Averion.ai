from fastapi.testclient import TestClient

from app.db.chat import StoredChatMessages
from app.db.documents import DatabaseNotConfiguredError
from app.main import app


client = TestClient(app)


def test_chat_endpoint_returns_answer_and_stores_messages(monkeypatch) -> None:
    stored_payload = {}

    def fake_retrieve_chunks(query: str, top_k: int) -> list[dict]:
        assert query == "What is the refund policy?"
        assert top_k > 0

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

    def fake_generate_answer(prompt: str) -> str:
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
        ]
    }
    assert stored_payload["conversation_id"] is None
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

    monkeypatch.setattr("app.api.chat.retrieve_chunks", lambda query, top_k: [])
    monkeypatch.setattr(
        "app.api.chat.build_rag_prompt",
        lambda question, chunks: "prompt without context"
    )
    monkeypatch.setattr(
        "app.api.chat.generate_answer",
        lambda prompt: "I don't know based on the available documents."
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


def test_chat_endpoint_returns_500_for_llm_provider_error(monkeypatch) -> None:
    monkeypatch.setattr("app.api.chat.retrieve_chunks", lambda query, top_k: [])
    monkeypatch.setattr("app.api.chat.build_rag_prompt", lambda question, chunks: "prompt")

    def fake_generate_answer(prompt: str) -> str:
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
    monkeypatch.setattr("app.api.chat.retrieve_chunks", lambda query, top_k: [])
    monkeypatch.setattr("app.api.chat.build_rag_prompt", lambda question, chunks: "prompt")
    monkeypatch.setattr("app.api.chat.generate_answer", lambda prompt: "answer")

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
