import pytest
from fastapi.testclient import TestClient

from app.core.auth import RequestContext, get_request_context
from app.core.config import settings
from app.db.documents import DatabaseNotConfiguredError
from app.db.users import (
    AccountProfile,
    AuthProfileCreate,
    UserProfile,
    get_user_profile_by_auth_id
)
from app.main import app


client = TestClient(app)


def test_auth_profile_create_defaults_to_member_role() -> None:
    profile = AuthProfileCreate(
        auth_user_id="00000000-0000-0000-0000-000000000401",
        email="teammate@example.com",
        organization_id=settings.default_organization_id
    )

    assert profile.role == "member"
    assert profile.name is None
    assert profile.avatar_url is None
    assert profile.job_title is None


def test_user_profile_carries_auth_mapping_fields() -> None:
    profile = UserProfile(
        user_id="00000000-0000-0000-0000-000000000501",
        organization_id=settings.default_organization_id,
        auth_user_id="00000000-0000-0000-0000-000000000401",
        email="teammate@example.com",
        name="Averion Teammate",
        avatar_url="https://example.com/avatar.png",
        job_title="Knowledge Manager",
        role="member"
    )

    assert profile.auth_user_id == "00000000-0000-0000-0000-000000000401"
    assert profile.email == "teammate@example.com"
    assert profile.name == "Averion Teammate"
    assert profile.avatar_url == "https://example.com/avatar.png"
    assert profile.job_title == "Knowledge Manager"


def test_allowed_email_domain_list_normalizes_config() -> None:
    original_domains = settings.allowed_email_domains
    settings.allowed_email_domains = " Gmail.com, googlemail.com ,, Example.com "

    try:
        assert settings.allowed_email_domain_list == [
            "gmail.com",
            "googlemail.com",
            "example.com"
        ]
    finally:
        settings.allowed_email_domains = original_domains


def test_get_user_profile_requires_database(monkeypatch) -> None:
    monkeypatch.setattr("app.db.users.is_database_configured", lambda: False)

    with pytest.raises(DatabaseNotConfiguredError, match="DATABASE_URL is not configured"):
        get_user_profile_by_auth_id("00000000-0000-0000-0000-000000000401")


def test_get_current_user_profile_returns_database_profile(monkeypatch) -> None:
    captured_scope = {}

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000501",
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="teammate@example.com",
            role="member",
            is_authenticated=True
        )

    def fake_get_account_profile(*, user_id: str, organization_id: str):
        captured_scope["user_id"] = user_id
        captured_scope["organization_id"] = organization_id

        return AccountProfile(
            user_id=user_id,
            organization_id=organization_id,
            organization_name="Development Organization",
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="teammate@example.com",
            name="Averion Teammate",
            avatar_url="https://example.com/avatar.png",
            job_title="Knowledge Manager",
            role="member"
        )

    monkeypatch.setattr("app.api.users.get_account_profile", fake_get_account_profile)
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.get("/users/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured_scope == {
        "user_id": "00000000-0000-0000-0000-000000000501",
        "organization_id": settings.default_organization_id
    }
    assert response.json()["email"] == "teammate@example.com"
    assert response.json()["name"] == "Averion Teammate"
    assert response.json()["job_title"] == "Knowledge Manager"
    assert response.json()["organization_name"] == "Development Organization"


def test_update_current_user_profile_updates_editable_fields(monkeypatch) -> None:
    captured_update = {}

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000501",
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="teammate@example.com",
            role="member",
            is_authenticated=True
        )

    def fake_update_account_profile(profile):
        captured_update["user_id"] = profile.user_id
        captured_update["organization_id"] = profile.organization_id
        captured_update["name"] = profile.name
        captured_update["job_title"] = profile.job_title

        return AccountProfile(
            user_id=profile.user_id,
            organization_id=profile.organization_id,
            organization_name="Development Organization",
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="teammate@example.com",
            name=profile.name,
            avatar_url=None,
            job_title=profile.job_title,
            role="member"
        )

    monkeypatch.setattr("app.api.users.update_account_profile", fake_update_account_profile)
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.patch(
            "/users/me",
            json={
                "name": "  Shubham Mitra  ",
                "job_title": "  Founder  "
            }
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured_update == {
        "user_id": "00000000-0000-0000-0000-000000000501",
        "organization_id": settings.default_organization_id,
        "name": "Shubham Mitra",
        "job_title": "Founder"
    }
    assert response.json()["name"] == "Shubham Mitra"
    assert response.json()["job_title"] == "Founder"


def test_update_current_user_profile_requires_profile() -> None:
    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id=None,
            auth_user_id=None,
            email=None,
            role=None,
            is_authenticated=False
        )

    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.patch(
            "/users/me",
            json={
                "name": "Averion Teammate",
                "job_title": "Knowledge Manager"
            }
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
