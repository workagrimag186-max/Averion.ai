from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.db.schema import DocumentFileType, DocumentStatus
from app.schemas.documents import DocumentUploadResponse


SUPPORTED_FILE_TYPES = {
    ".pdf": DocumentFileType.PDF,
    ".txt": DocumentFileType.TXT,
    ".docx": DocumentFileType.DOCX
}


class UnsupportedDocumentTypeError(ValueError):
    pass


def get_file_type(filename: str) -> DocumentFileType:
    suffix = Path(filename).suffix.lower()

    try:
        return SUPPORTED_FILE_TYPES[suffix]
    except KeyError as exc:
        raise UnsupportedDocumentTypeError(
            "Unsupported file type. Upload a PDF, TXT, or DOCX file."
        ) from exc


def build_storage_path(upload_dir: str, document_id: str, filename: str) -> Path:
    safe_filename = Path(filename).name
    return Path(upload_dir) / document_id / safe_filename


async def save_uploaded_document(
    file: UploadFile,
    upload_dir: str
) -> DocumentUploadResponse:
    file_type = get_file_type(file.filename or "")
    document_id = str(uuid4())
    storage_path = build_storage_path(upload_dir, document_id, file.filename or "document")

    storage_path.parent.mkdir(parents=True, exist_ok=True)

    contents = await file.read()
    storage_path.write_bytes(contents)

    return DocumentUploadResponse(
        document_id=document_id,
        filename=Path(file.filename or storage_path.name).name,
        file_type=file_type.value,
        status=DocumentStatus.UPLOADED.value,
        storage_path=str(storage_path)
    )
