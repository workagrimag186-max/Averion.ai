import pytest
from fastapi.testclient import TestClient

from app.core.auth import RequestContext, get_request_context
from app.core.config import settings
from app.db.documents import DatabaseNotConfiguredError
from app.db.users import (
    AccountProfile,
    AuthProfileCreate,
    OrganizationInvitation,
    Team,
    TeamMember,
    UserProfile,
    get_or_create_user_profile,
    get_user_profile_by_auth_id
)
from app.main import app


client = TestClient(app)


class FakeCursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=None):
        self.statements.append((query, params))

    def fetchone(self):
        return self.rows.pop(0)


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return self._cursor


def test_auth_profile_create_defaults_to_member_role() -> None:
    profile = AuthProfileCreate(
        auth_user_id="00000000-0000-0000-0000-000000000401",
        email="teammate@example.com"
    )

    assert profile.organization_id is None
    assert profile.role == "owner"
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


def test_get_or_create_user_profile_creates_private_owner_workspace(monkeypatch) -> None:
    private_organization_id = "00000000-0000-0000-0000-000000000601"
    created_user_id = "00000000-0000-0000-0000-000000000602"
    cursor = FakeCursor(
        rows=[
            None,
            (private_organization_id,),
            (
                created_user_id,
                private_organization_id,
                "00000000-0000-0000-0000-000000000401",
                "teammate@example.com",
                "Averion Teammate",
                "https://example.com/avatar.png",
                None,
                "owner"
            )
        ]
    )

    monkeypatch.setattr("app.db.users.is_database_configured", lambda: True)
    monkeypatch.setattr(
        "app.db.users.psycopg.connect",
        lambda *_args, **_kwargs: FakeConnection(cursor)
    )

    profile = get_or_create_user_profile(
        AuthProfileCreate(
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="teammate@example.com",
            name="Averion Teammate",
            avatar_url="https://example.com/avatar.png"
        )
    )

    assert profile.organization_id == private_organization_id
    assert profile.role == "owner"
    assert cursor.statements[1][1] == ("Averion Teammate's Workspace",)
    assert cursor.statements[2][1] == (
        private_organization_id,
        "00000000-0000-0000-0000-000000000401",
        "teammate@example.com",
        "Averion Teammate",
        "https://example.com/avatar.png",
        None,
        "owner"
    )


def test_get_or_create_user_profile_keeps_existing_workspace(monkeypatch) -> None:
    existing_organization_id = "00000000-0000-0000-0000-000000000701"
    existing_user_id = "00000000-0000-0000-0000-000000000702"
    existing_row = (
        existing_user_id,
        existing_organization_id,
        "00000000-0000-0000-0000-000000000401",
        "teammate@example.com",
        "Existing Name",
        None,
        None,
        "member"
    )
    updated_row = (
        existing_user_id,
        existing_organization_id,
        "00000000-0000-0000-0000-000000000401",
        "teammate@example.com",
        "Existing Name",
        "https://example.com/avatar.png",
        None,
        "member"
    )
    cursor = FakeCursor(rows=[existing_row, updated_row])

    monkeypatch.setattr("app.db.users.is_database_configured", lambda: True)
    monkeypatch.setattr(
        "app.db.users.psycopg.connect",
        lambda *_args, **_kwargs: FakeConnection(cursor)
    )

    profile = get_or_create_user_profile(
        AuthProfileCreate(
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="teammate@example.com",
            name="New Name From OAuth",
            avatar_url="https://example.com/avatar.png"
        )
    )

    assert profile.organization_id == existing_organization_id
    assert profile.name == "Existing Name"
    assert profile.role == "member"
    assert len(cursor.statements) == 2


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


def test_get_current_user_team_returns_organization_members(monkeypatch) -> None:
    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000501",
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="owner@example.com",
            role="owner",
            is_authenticated=True
        )

    def fake_get_team(organization_id: str):
        assert organization_id == settings.default_organization_id

        return Team(
            organization_id=organization_id,
            organization_name="Averion.ai",
            members=[
                TeamMember(
                    user_id="00000000-0000-0000-0000-000000000501",
                    email="owner@example.com",
                    name="Owner User",
                    job_title="Founder",
                    role="owner"
                ),
                TeamMember(
                    user_id="00000000-0000-0000-0000-000000000502",
                    email="member@example.com",
                    name="Member User",
                    job_title=None,
                    role="member"
                )
            ]
        )

    monkeypatch.setattr("app.api.users.get_team", fake_get_team)
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.get("/users/team")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["organization_name"] == "Averion.ai"
    assert [member["role"] for member in response.json()["members"]] == [
        "owner",
        "member"
    ]


def test_member_cannot_update_organization_name() -> None:
    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000502",
            auth_user_id="00000000-0000-0000-0000-000000000402",
            email="member@example.com",
            role="member",
            is_authenticated=True
        )

    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.patch(
            "/users/organization",
            json={"name": "Averion.ai"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Only organization owners can manage workspace settings."
    }


def test_owner_can_update_organization_name(monkeypatch) -> None:
    captured_update = {}

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000501",
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="owner@example.com",
            role="owner",
            is_authenticated=True
        )

    def fake_update_organization_name(*, organization_id: str, name: str):
        captured_update["organization_id"] = organization_id
        captured_update["name"] = name

        return Team(
            organization_id=organization_id,
            organization_name=name,
            members=[]
        )

    monkeypatch.setattr(
        "app.api.users.update_organization_name",
        fake_update_organization_name
    )
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.patch(
            "/users/organization",
            json={"name": "  Averion.ai  "}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured_update == {
        "organization_id": settings.default_organization_id,
        "name": "Averion.ai"
    }
    assert response.json()["organization_name"] == "Averion.ai"


def test_owner_can_update_team_member_role(monkeypatch) -> None:
    captured_update = {}

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000501",
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="owner@example.com",
            role="owner",
            is_authenticated=True
        )

    def fake_update_team_member_role(*, organization_id: str, user_id: str, role: str):
        captured_update["organization_id"] = organization_id
        captured_update["user_id"] = user_id
        captured_update["role"] = role

        return TeamMember(
            user_id=user_id,
            email="member@example.com",
            name="Member User",
            job_title=None,
            role=role
        )

    monkeypatch.setattr(
        "app.api.users.update_team_member_role",
        fake_update_team_member_role
    )
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.patch(
            "/users/team/00000000-0000-0000-0000-000000000502/role",
            json={"role": "owner"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured_update == {
        "organization_id": settings.default_organization_id,
        "user_id": "00000000-0000-0000-0000-000000000502",
        "role": "owner"
    }
    assert response.json()["role"] == "owner"


def test_owner_can_demote_another_owner(monkeypatch) -> None:
    captured_update = {}

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000501",
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="owner@example.com",
            role="owner",
            is_authenticated=True
        )

    def fake_update_team_member_role(*, organization_id: str, user_id: str, role: str):
        captured_update["organization_id"] = organization_id
        captured_update["user_id"] = user_id
        captured_update["role"] = role

        return TeamMember(
            user_id=user_id,
            email="co-owner@example.com",
            name="Co Owner",
            job_title=None,
            role=role
        )

    monkeypatch.setattr(
        "app.api.users.update_team_member_role",
        fake_update_team_member_role
    )
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.patch(
            "/users/team/00000000-0000-0000-0000-000000000503/role",
            json={"role": "member"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured_update == {
        "organization_id": settings.default_organization_id,
        "user_id": "00000000-0000-0000-0000-000000000503",
        "role": "member"
    }
    assert response.json()["role"] == "member"


def test_member_cannot_update_team_member_role() -> None:
    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000502",
            auth_user_id="00000000-0000-0000-0000-000000000402",
            email="member@example.com",
            role="member",
            is_authenticated=True
        )

    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.patch(
            "/users/team/00000000-0000-0000-0000-000000000501/role",
            json={"role": "member"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Only organization owners can manage workspace settings."
    }


def test_owner_cannot_update_own_role() -> None:
    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000501",
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="owner@example.com",
            role="owner",
            is_authenticated=True
        )

    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.patch(
            "/users/team/00000000-0000-0000-0000-000000000501/role",
            json={"role": "member"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json() == {"detail": "Owners cannot change their own role."}


def test_owner_can_create_organization_invitation(monkeypatch) -> None:
    captured_invitation = {}

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000501",
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="owner@example.com",
            role="owner",
            is_authenticated=True
        )

    def fake_create_organization_invitation(
        *,
        organization_id: str,
        invited_by_user_id: str,
        invited_email: str
    ):
        captured_invitation["organization_id"] = organization_id
        captured_invitation["invited_by_user_id"] = invited_by_user_id
        captured_invitation["invited_email"] = invited_email

        return OrganizationInvitation(
            invitation_id="00000000-0000-0000-0000-000000000601",
            organization_id=organization_id,
            organization_name="Averion.ai",
            invited_email=invited_email,
            invited_by_user_id=invited_by_user_id,
            status="pending",
            expires_at="2026-06-08T00:00:00+00:00",
            created_at="2026-06-01T00:00:00+00:00"
        )

    monkeypatch.setattr(
        "app.api.users.create_organization_invitation",
        fake_create_organization_invitation
    )
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.post(
            "/users/invitations",
            json={"email": "  Friend@Example.com  "}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured_invitation == {
        "organization_id": settings.default_organization_id,
        "invited_by_user_id": "00000000-0000-0000-0000-000000000501",
        "invited_email": "friend@example.com"
    }
    assert response.json()["status"] == "pending"


def test_member_cannot_create_organization_invitation() -> None:
    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000502",
            auth_user_id="00000000-0000-0000-0000-000000000402",
            email="member@example.com",
            role="member",
            is_authenticated=True
        )

    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.post(
            "/users/invitations",
            json={"email": "friend@example.com"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_user_can_accept_matching_invitation(monkeypatch) -> None:
    captured_accept = {}

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id="00000000-0000-0000-0000-000000000777",
            user_id="00000000-0000-0000-0000-000000000502",
            auth_user_id="00000000-0000-0000-0000-000000000402",
            email="friend@example.com",
            role="owner",
            is_authenticated=True
        )

    def fake_accept_organization_invitation(
        *,
        invitation_id: str,
        user_id: str,
        email: str
    ):
        captured_accept["invitation_id"] = invitation_id
        captured_accept["user_id"] = user_id
        captured_accept["email"] = email

        return UserProfile(
            user_id=user_id,
            organization_id=settings.default_organization_id,
            auth_user_id="00000000-0000-0000-0000-000000000402",
            email=email,
            name="Friend User",
            avatar_url=None,
            job_title=None,
            role="member"
        )

    monkeypatch.setattr(
        "app.api.users.accept_organization_invitation",
        fake_accept_organization_invitation
    )
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.post(
            "/users/invitations/00000000-0000-0000-0000-000000000601/accept"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured_accept == {
        "invitation_id": "00000000-0000-0000-0000-000000000601",
        "user_id": "00000000-0000-0000-0000-000000000502",
        "email": "friend@example.com"
    }
    assert response.json()["organization_id"] == settings.default_organization_id
    assert response.json()["role"] == "member"


def test_owner_can_remove_team_member(monkeypatch) -> None:
    captured_remove = {}

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000501",
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="owner@example.com",
            role="owner",
            is_authenticated=True
        )

    def fake_remove_team_member_from_organization(
        *,
        organization_id: str,
        user_id: str
    ):
        captured_remove["organization_id"] = organization_id
        captured_remove["user_id"] = user_id

        return TeamMember(
            user_id=user_id,
            email="member@example.com",
            name="Member User",
            job_title=None,
            role="member"
        )

    monkeypatch.setattr(
        "app.api.users.remove_team_member_from_organization",
        fake_remove_team_member_from_organization
    )
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.delete(
            "/users/team/00000000-0000-0000-0000-000000000502"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured_remove == {
        "organization_id": settings.default_organization_id,
        "user_id": "00000000-0000-0000-0000-000000000502"
    }
    assert response.json()["email"] == "member@example.com"


def test_owner_cannot_remove_self() -> None:
    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000501",
            auth_user_id="00000000-0000-0000-0000-000000000401",
            email="owner@example.com",
            role="owner",
            is_authenticated=True
        )

    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.delete(
            "/users/team/00000000-0000-0000-0000-000000000501"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json() == {"detail": "Owners cannot remove themselves."}
