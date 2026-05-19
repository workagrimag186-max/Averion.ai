from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    question: str = Field(..., min_length=1)


class ChatCitation(BaseModel):
    document_id: str
    chunk_index: int
    chunk_id: str
    filename: str
    page_number: int | None = None
    snippet: str
    score: float | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    citations: list[ChatCitation]
