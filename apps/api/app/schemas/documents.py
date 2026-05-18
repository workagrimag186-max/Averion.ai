from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    status: str
    storage_path: str
    metadata_stored: bool = False
    chunks_stored: int = 0
