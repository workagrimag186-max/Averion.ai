from fastapi.testclient import TestClient

from app.db.documents import DatabaseNotConfiguredError
from app.db.feedback import FeedbackMessageNotFoundError, FeedbackRecord
from app.db.schema import FeedbackRating
from app.main import app


client = TestClient(app)


def test_create_feedback_stores_assistant_message_feedback(monkeypatch) -> None:
    stored_payload = {}

    def fake_store_feedback(feedback) -> FeedbackRecord:
        stored_payload["message_id"] = feedback.message_id
        stored_payload["rating"] = feedback.rating
        stored_payload["user_id"] = feedback.user_id
        stored_payload["correction_text"] = feedback.correction_text

        return FeedbackRecord(
            feedback_id="00000000-0000-0000-0000-000000000201",
            message_id=feedback.message_id,
            user_id=feedback.user_id,
            rating=feedback.rating,
            correction_text=feedback.correction_text,
            created_at="2026-05-20 10:00:00+00"
        )

    monkeypatch.setattr("app.api.feedback.store_feedback", fake_store_feedback)

    response = client.post(
        "/feedback",
        json={
            "message_id": "00000000-0000-0000-0000-000000000101",
            "rating": "down",
            "user_id": "00000000-0000-0000-0000-000000000301",
            "correction_text": "Use the source quote from page 2."
        }
    )

    assert response.status_code == 201
    assert response.json() == {
        "feedback_id": "00000000-0000-0000-0000-000000000201",
        "message_id": "00000000-0000-0000-0000-000000000101",
        "user_id": "00000000-0000-0000-0000-000000000301",
        "rating": "down",
        "correction_text": "Use the source quote from page 2.",
        "created_at": "2026-05-20 10:00:00+00"
    }
    assert stored_payload == {
        "message_id": "00000000-0000-0000-0000-000000000101",
        "rating": FeedbackRating.DOWN,
        "user_id": "00000000-0000-0000-0000-000000000301",
        "correction_text": "Use the source quote from page 2."
    }


def test_create_feedback_normalizes_empty_correction_text(monkeypatch) -> None:
    stored_payload = {}

    def fake_store_feedback(feedback) -> FeedbackRecord:
        stored_payload["correction_text"] = feedback.correction_text

        return FeedbackRecord(
            feedback_id="00000000-0000-0000-0000-000000000202",
            message_id=feedback.message_id,
            user_id=None,
            rating=feedback.rating,
            correction_text=feedback.correction_text,
            created_at="2026-05-20 10:01:00+00"
        )

    monkeypatch.setattr("app.api.feedback.store_feedback", fake_store_feedback)

    response = client.post(
        "/feedback",
        json={
            "message_id": "00000000-0000-0000-0000-000000000102",
            "rating": "up",
            "correction_text": "   "
        }
    )

    assert response.status_code == 201
    assert response.json()["correction_text"] is None
    assert stored_payload["correction_text"] is None


def test_create_feedback_returns_404_for_unknown_message(monkeypatch) -> None:
    def fake_store_feedback(feedback) -> FeedbackRecord:
        raise FeedbackMessageNotFoundError("Assistant message not found for feedback.")

    monkeypatch.setattr("app.api.feedback.store_feedback", fake_store_feedback)

    response = client.post(
        "/feedback",
        json={
            "message_id": "00000000-0000-0000-0000-000000000999",
            "rating": "up"
        }
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Assistant message not found for feedback."}


def test_create_feedback_returns_422_for_invalid_rating() -> None:
    response = client.post(
        "/feedback",
        json={
            "message_id": "00000000-0000-0000-0000-000000000101",
            "rating": "maybe"
        }
    )

    assert response.status_code == 422


def test_create_feedback_returns_503_when_database_is_not_configured(monkeypatch) -> None:
    def fake_store_feedback(feedback) -> FeedbackRecord:
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    monkeypatch.setattr("app.api.feedback.store_feedback", fake_store_feedback)

    response = client.post(
        "/feedback",
        json={
            "message_id": "00000000-0000-0000-0000-000000000101",
            "rating": "up"
        }
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "DATABASE_URL is not configured."}


def test_list_feedback_returns_queryable_records(monkeypatch) -> None:
    def fake_list_feedback(limit: int) -> list[FeedbackRecord]:
        assert limit == 2

        return [
            FeedbackRecord(
                feedback_id="00000000-0000-0000-0000-000000000203",
                message_id="00000000-0000-0000-0000-000000000103",
                user_id=None,
                rating=FeedbackRating.DOWN,
                correction_text="Answer should mention onboarding.",
                created_at="2026-05-20 10:02:00+00"
            )
        ]

    monkeypatch.setattr("app.api.feedback.list_feedback", fake_list_feedback)

    response = client.get("/feedback?limit=2")

    assert response.status_code == 200
    assert response.json() == [
        {
            "feedback_id": "00000000-0000-0000-0000-000000000203",
            "message_id": "00000000-0000-0000-0000-000000000103",
            "user_id": None,
            "rating": "down",
            "correction_text": "Answer should mention onboarding.",
            "created_at": "2026-05-20 10:02:00+00"
        }
    ]

