from dataclasses import dataclass

import psycopg

from app.core.config import settings
from app.db.connection import is_database_configured
from app.db.documents import DatabaseNotConfiguredError
from app.db.schema import FeedbackRating, MessageRole


class FeedbackMessageNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class FeedbackCreate:
    message_id: str
    rating: FeedbackRating
    user_id: str | None = None
    correction_text: str | None = None


@dataclass(frozen=True)
class FeedbackRecord:
    feedback_id: str
    message_id: str
    user_id: str | None
    rating: FeedbackRating
    correction_text: str | None
    created_at: str


def store_feedback(feedback: FeedbackCreate) -> FeedbackRecord:
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select id
                from messages
                where id = %s::uuid
                    and role = %s
                """,
                (
                    feedback.message_id,
                    MessageRole.ASSISTANT.value
                )
            )

            if cursor.fetchone() is None:
                raise FeedbackMessageNotFoundError(
                    "Assistant message not found for feedback."
                )

            cursor.execute(
                """
                insert into feedback (
                    message_id,
                    user_id,
                    rating,
                    correction_text
                )
                values (%s::uuid, %s::uuid, %s, %s)
                returning
                    id::text,
                    message_id::text,
                    user_id::text,
                    rating,
                    correction_text,
                    created_at::text
                """,
                (
                    feedback.message_id,
                    feedback.user_id,
                    feedback.rating.value,
                    feedback.correction_text
                )
            )

            row = cursor.fetchone()

    if row is None:
        raise RuntimeError("Feedback insert did not return a record.")

    return FeedbackRecord(
        feedback_id=row[0],
        message_id=row[1],
        user_id=row[2],
        rating=FeedbackRating(row[3]),
        correction_text=row[4],
        created_at=row[5]
    )


def list_feedback(limit: int = 50) -> list[FeedbackRecord]:
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select
                    id::text,
                    message_id::text,
                    user_id::text,
                    rating,
                    correction_text,
                    created_at::text
                from feedback
                order by created_at desc
                limit %s
                """,
                (limit,)
            )

            return [
                FeedbackRecord(
                    feedback_id=row[0],
                    message_id=row[1],
                    user_id=row[2],
                    rating=FeedbackRating(row[3]),
                    correction_text=row[4],
                    created_at=row[5]
                )
                for row in cursor.fetchall()
            ]

