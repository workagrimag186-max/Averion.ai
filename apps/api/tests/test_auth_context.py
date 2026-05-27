from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.auth import get_request_context
from app.core.config import settings
from app.db.users import UserProfile
from app.main import app


TEST_SECRET = "test-secret-with-at-least-thirty-two-characters"
client = TestClient(app)


def _token(secret: str, **claims) -> str:
    payload = {
        "sub": "00000000-0000-0000-0000-000000000701",
        "email": "teammate@example.com",
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "user_metadata": {
            "full_name": "Averion Teammate",
            "avatar_url": "https://example.com/avatar.png"
        },
        **claims
    }

    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture(autouse=True)
def restore_auth_settings():
    original_auth_required = settings.auth_required
    original_jwt_secret = settings.supabase_jwt_secret
    original_domains = settings.allowed_email_domains

    yield

    settings.auth_required = original_auth_required
    settings.supabase_jwt_secret = original_jwt_secret
    settings.allowed_email_domains = original_domains


def test_request_context_uses_development_fallback_without_token() -> None:
    settings.auth_required = False

    context = get_request_context()

    assert context.organization_id == settings.default_organization_id
    assert context.user_id is None
    assert context.is_authenticated is False


def test_request_context_requires_token_when_auth_required() -> None:
    settings.auth_required = True

    with pytest.raises(HTTPException) as exc_info:
        get_request_context()

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authentication required."


def test_request_context_rejects_invalid_authorization_header() -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_request_context(authorization="Token abc")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authorization header."


def test_request_context_rejects_invalid_token() -> None:
    settings.supabase_jwt_secret = TEST_SECRET

    with pytest.raises(HTTPException) as exc_info:
        get_request_context(authorization="Bearer not-a-jwt")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication token."


def test_request_context_builds_authenticated_context_without_database(monkeypatch) -> None:
    settings.auth_required = False
    settings.supabase_jwt_secret = TEST_SECRET
    token = _token(settings.supabase_jwt_secret)

    monkeypatch.setattr("app.core.auth.is_database_configured", lambda: False)

    context = get_request_context(authorization=f"Bearer {token}")

    assert context.organization_id == settings.default_organization_id
    assert context.auth_user_id == "00000000-0000-0000-0000-000000000701"
    assert context.email == "teammate@example.com"
    assert context.is_authenticated is True


def test_request_context_creates_profile_when_database_is_configured(monkeypatch) -> None:
    settings.supabase_jwt_secret = TEST_SECRET
    token = _token(settings.supabase_jwt_secret)
    captured_profile = {}

    def fake_get_or_create_user_profile(profile):
        captured_profile["auth_user_id"] = profile.auth_user_id
        captured_profile["email"] = profile.email
        captured_profile["organization_id"] = profile.organization_id
        captured_profile["name"] = profile.name
        captured_profile["avatar_url"] = profile.avatar_url

        return UserProfile(
            user_id="00000000-0000-0000-0000-000000000801",
            organization_id=settings.default_organization_id,
            auth_user_id=profile.auth_user_id,
            email=profile.email,
            name=profile.name,
            avatar_url=profile.avatar_url,
            job_title=None,
            role="member"
        )

    monkeypatch.setattr("app.core.auth.is_database_configured", lambda: True)
    monkeypatch.setattr(
        "app.core.auth.get_or_create_user_profile",
        fake_get_or_create_user_profile
    )

    context = get_request_context(authorization=f"Bearer {token}")

    assert captured_profile == {
        "auth_user_id": "00000000-0000-0000-0000-000000000701",
        "email": "teammate@example.com",
        "organization_id": settings.default_organization_id,
        "name": "Averion Teammate",
        "avatar_url": "https://example.com/avatar.png"
    }
    assert context.user_id == "00000000-0000-0000-0000-000000000801"
    assert context.organization_id == settings.default_organization_id
    assert context.email == "teammate@example.com"
    assert context.role == "member"
    assert context.is_authenticated is True


def test_request_context_rejects_disallowed_email_domain() -> None:
    settings.supabase_jwt_secret = TEST_SECRET
    settings.allowed_email_domains = "gmail.com"
    token = _token(settings.supabase_jwt_secret, email="teammate@example.com")

    with pytest.raises(HTTPException) as exc_info:
        get_request_context(authorization=f"Bearer {token}")

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Email domain is not allowed."


def test_documents_route_rejects_missing_token_when_auth_required() -> None:
    settings.auth_required = True

    response = client.get("/documents")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}
