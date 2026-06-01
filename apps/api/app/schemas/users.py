from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AccountProfileResponse(BaseModel):
    user_id: str | None
    organization_id: str
    organization_name: str | None
    auth_user_id: str | None
    email: str | None
    name: str | None
    avatar_url: str | None
    job_title: str | None
    role: str | None


class AccountProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    job_title: str | None = Field(default=None, max_length=120)

    @field_validator("name", "job_title")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()
        return stripped_value or None


class TeamMemberResponse(BaseModel):
    user_id: str
    email: str
    name: str | None
    job_title: str | None
    role: Literal["owner", "member"]


class TeamResponse(BaseModel):
    organization_id: str
    organization_name: str
    members: list[TeamMemberResponse]


class OrganizationUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("Organization name is required.")

        return stripped_value


class TeamMemberRoleUpdateRequest(BaseModel):
    role: Literal["owner", "member"]


class OrganizationInvitationCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        stripped_value = value.strip().lower()

        if "@" not in stripped_value:
            raise ValueError("Enter a valid email address.")

        return stripped_value


class OrganizationInvitationResponse(BaseModel):
    invitation_id: str
    organization_id: str
    organization_name: str
    invited_email: str
    invited_by_user_id: str
    status: Literal["pending", "accepted", "revoked", "expired"]
    expires_at: str
    created_at: str
    accepted_at: str | None = None
    accepted_by_user_id: str | None = None
