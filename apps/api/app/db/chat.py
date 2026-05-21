import json
import uuid
from dataclasses import dataclass
from typing import Any

import psycopg

from app.core.config import settings
from app.db.connection import is_database_configured
from app.db.documents import DatabaseNotConfiguredError
from app.db.schema import MessageRole


class ConversationNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class StoredChatMessages:
    conversation_id: str
    user_message_id: str
    assistant_message_id: str


def _ensure_development_organization(cursor) -> None:
    cursor.execute(
        """
        insert into organizations (id, name)
        values (%s::uuid, %s)
        on conflict (id) do nothing
        """,
        (
            settings.default_organization_id,
            "Development Organization"
        )
    )


def store_chat_exchange(
    *,
    organization_id: str,
    conversation_id: str | None,
    question: str,
    answer: str,
    citations: list[dict[str, Any]]
) -> StoredChatMessages:
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    resolved_conversation_id = conversation_id or str(uuid.uuid4())
    user_message_id = str(uuid.uuid4())
    assistant_message_id = str(uuid.uuid4())

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            if organization_id == settings.default_organization_id:
                _ensure_development_organization(cursor)

            if conversation_id is None:
                cursor.execute(
                    """
                    insert into conversations (id, organization_id, title)
                    values (%s::uuid, %s::uuid, %s)
                    """,
                    (
                        resolved_conversation_id,
                        organization_id,
                        question[:80]
                    )
                )
            else:
                cursor.execute(
                    """
                    select id
                    from conversations
                    where id = %s::uuid
                        and organization_id = %s::uuid
                    """,
                    (
                        resolved_conversation_id,
                        organization_id
                    )
                )

                if cursor.fetchone() is None:
                    raise ConversationNotFoundError(
                        "Conversation not found for this organization."
                    )

            cursor.execute(
                """
                insert into messages (id, conversation_id, role, content, citations)
                values (%s::uuid, %s::uuid, %s, %s, %s::jsonb)
                """,
                (
                    user_message_id,
                    resolved_conversation_id,
                    MessageRole.USER.value,
                    question,
                    "[]"
                )
            )

            cursor.execute(
                """
                insert into messages (id, conversation_id, role, content, citations)
                values (%s::uuid, %s::uuid, %s, %s, %s::jsonb)
                """,
                (
                    assistant_message_id,
                    resolved_conversation_id,
                    MessageRole.ASSISTANT.value,
                    answer,
                    json.dumps(citations)
                )
            )

            cursor.execute(
                """
                update conversations
                set updated_at = now()
                where id = %s::uuid
                    and organization_id = %s::uuid
                """,
                (
                    resolved_conversation_id,
                    organization_id
                )
            )

    return StoredChatMessages(
        conversation_id=resolved_conversation_id,
        user_message_id=user_message_id,
        assistant_message_id=assistant_message_id
    )
