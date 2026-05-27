import pytest

from app.core.config import settings
from app.db.documents import DatabaseNotConfiguredError
from app.db.users import AuthProfileCreate, UserProfile, get_user_profile_by_auth_id


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
