from pydantic import BaseModel


class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    file_type: str
    status: str
    storage_path: str
    chunks_count: int = 0
    error_message: str | None = None
    created_at: str
    updated_at: str


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    status: str
    storage_path: str
    metadata_stored: bool = False
    chunks_stored: int = 0
