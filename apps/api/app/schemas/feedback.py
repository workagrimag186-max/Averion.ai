from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.db.schema import FeedbackRating


class FeedbackRequest(BaseModel):
    message_id: UUID
    rating: FeedbackRating
    user_id: UUID | None = None
    correction_text: str | None = Field(default=None, max_length=5000)

    @field_validator("correction_text")
    @classmethod
    def normalize_correction_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()
        return stripped_value or None


class FeedbackResponse(BaseModel):
    feedback_id: str
    message_id: str
    user_id: str | None
    rating: FeedbackRating
    correction_text: str | None
    created_at: str

