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
