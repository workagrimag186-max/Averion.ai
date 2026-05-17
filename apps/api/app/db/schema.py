from enum import StrEnum


class TableName(StrEnum):
    ORGANIZATIONS = "organizations"
    USERS = "users"
    DOCUMENTS = "documents"
    DOCUMENT_CHUNKS = "document_chunks"
    CONVERSATIONS = "conversations"
    MESSAGES = "messages"
    FEEDBACK = "feedback"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DocumentFileType(StrEnum):
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"


class UserRole(StrEnum):
    OWNER = "owner"
    MEMBER = "member"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class FeedbackRating(StrEnum):
    UP = "up"
    DOWN = "down"


MVP_TABLES = tuple(table.value for table in TableName)
