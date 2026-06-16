import logging

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_security_headers_are_attached_to_api_responses() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert "camera=()" in response.headers["Permissions-Policy"]


def test_request_id_is_generated_or_preserved() -> None:
    generated_response = client.get("/health")
    provided_response = client.get(
        "/health",
        headers={"X-Request-ID": "request-test-123"}
    )

    assert generated_response.headers["X-Request-ID"]
    assert provided_response.headers["X-Request-ID"] == "request-test-123"


def test_request_completion_is_logged_without_authorization_header(caplog) -> None:
    caplog.set_level(logging.INFO, logger="averion.api")

    response = client.get(
        "/health",
        headers={
            "Authorization": "Bearer secret-token",
            "X-Request-ID": "request-log-123"
        }
    )

    assert response.status_code == 200
    record = next(
        record
        for record in caplog.records
        if record.name == "averion.api" and record.message == "request_completed"
    )
    assert record.request_id == "request-log-123"
    assert record.method == "GET"
    assert record.path == "/health"
    assert record.status_code == 200
    assert isinstance(record.duration_ms, float)
    assert "secret-token" not in record.getMessage()
