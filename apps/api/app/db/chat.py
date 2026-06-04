import json
import uuid
from dataclasses import dataclass
from datetime import datetime
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


@dataclass(frozen=True)
class ConversationSummary:
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


@dataclass(frozen=True)
class Message:
    id: str
    role: str
    content: str
    citations: list[dict[str, Any]]
    created_at: datetime


@dataclass(frozen=True)
class ConversationDetail:
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[Message]


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
    user_id: str | None,
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
                # Generate title from the first question
                title = generate_conversation_title(question)
                
                cursor.execute(
                    """
                    insert into conversations (id, organization_id, user_id, title)
                    values (%s::uuid, %s::uuid, %s::uuid, %s)
                    """,
                    (
                        resolved_conversation_id,
                        organization_id,
                        user_id,
                        title
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



def get_conversations(
    *,
    organization_id: str,
    user_id: str | None = None
) -> list[ConversationSummary]:
    """
    Retrieve all conversations for an organization, optionally filtered by user.
    Returns conversations ordered by most recently updated first.
    """
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            if user_id:
                cursor.execute(
                    """
                    select 
                        c.id,
                        c.title,
                        c.created_at,
                        c.updated_at,
                        count(m.id) as message_count
                    from conversations c
                    left join messages m on m.conversation_id = c.id
                    where c.organization_id = %s::uuid
                        and c.user_id = %s::uuid
                    group by c.id, c.title, c.created_at, c.updated_at
                    order by c.updated_at desc
                    """,
                    (organization_id, user_id)
                )
            else:
                cursor.execute(
                    """
                    select 
                        c.id,
                        c.title,
                        c.created_at,
                        c.updated_at,
                        count(m.id) as message_count
                    from conversations c
                    left join messages m on m.conversation_id = c.id
                    where c.organization_id = %s::uuid
                    group by c.id, c.title, c.created_at, c.updated_at
                    order by c.updated_at desc
                    """,
                    (organization_id,)
                )

            rows = cursor.fetchall()
            return [
                ConversationSummary(
                    id=str(row[0]),
                    title=row[1] or "Untitled Conversation",
                    created_at=row[2],
                    updated_at=row[3],
                    message_count=row[4]
                )
                for row in rows
            ]


def get_conversation_by_id(
    *,
    conversation_id: str,
    organization_id: str
) -> ConversationDetail:
    """
    Retrieve a specific conversation with all its messages.
    Enforces organization isolation.
    """
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            # Get conversation details
            cursor.execute(
                """
                select id, title, created_at, updated_at
                from conversations
                where id = %s::uuid
                    and organization_id = %s::uuid
                """,
                (conversation_id, organization_id)
            )

            row = cursor.fetchone()
            if row is None:
                raise ConversationNotFoundError(
                    "Conversation not found for this organization."
                )

            # Get all messages for this conversation
            cursor.execute(
                """
                select id, role, content, citations, created_at
                from messages
                where conversation_id = %s::uuid
                order by created_at asc
                """,
                (conversation_id,)
            )

            message_rows = cursor.fetchall()
            messages = [
                Message(
                    id=str(msg_row[0]),
                    role=msg_row[1],
                    content=msg_row[2],
                    citations=msg_row[3] if msg_row[3] else [],
                    created_at=msg_row[4]
                )
                for msg_row in message_rows
            ]

            return ConversationDetail(
                id=str(row[0]),
                title=row[1] or "Untitled Conversation",
                created_at=row[2],
                updated_at=row[3],
                messages=messages
            )


def delete_conversation(
    *,
    conversation_id: str,
    organization_id: str
) -> None:
    """
    Delete a conversation and all its messages.
    Enforces organization isolation.
    """
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            # Verify conversation belongs to organization before deleting
            cursor.execute(
                """
                delete from conversations
                where id = %s::uuid
                    and organization_id = %s::uuid
                returning id
                """,
                (conversation_id, organization_id)
            )

            if cursor.fetchone() is None:
                raise ConversationNotFoundError(
                    "Conversation not found for this organization."
                )


def update_conversation_title(
    *,
    conversation_id: str,
    organization_id: str,
    title: str
) -> None:
    """
    Update the title of a conversation.
    Enforces organization isolation.
    """
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                update conversations
                set title = %s, updated_at = now()
                where id = %s::uuid
                    and organization_id = %s::uuid
                returning id
                """,
                (title, conversation_id, organization_id)
            )

            if cursor.fetchone() is None:
                raise ConversationNotFoundError(
                    "Conversation not found for this organization."
                )


def generate_conversation_title(question: str) -> str:
    """
    Generate a conversation title from the first question.
    Truncates to 80 characters and adds ellipsis if needed.
    """
    # Clean up the question
    cleaned = question.strip()
    
    # If question is short enough, use it as-is
    if len(cleaned) <= 80:
        return cleaned
    
    # Truncate and add ellipsis
    return cleaned[:77] + "..."
