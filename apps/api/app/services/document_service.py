from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.db.schema import DocumentFileType, DocumentStatus
from app.db.connection import is_database_configured
from app.db.documents import DocumentMetadataCreate, create_document_metadata
from app.schemas.documents import DocumentUploadResponse


SUPPORTED_FILE_TYPES = {
    ".pdf": DocumentFileType.PDF,
    ".txt": DocumentFileType.TXT,
    ".docx": DocumentFileType.DOCX
}


class UnsupportedDocumentTypeError(ValueError):
    pass


class DocumentMetadataStorageError(RuntimeError):
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
    upload_dir: str,
    organization_id: str
) -> DocumentUploadResponse:
    file_type = get_file_type(file.filename or "")
    document_id = str(uuid4())
    filename = Path(file.filename or "document").name
    storage_path = build_storage_path(upload_dir, document_id, filename)

    storage_path.parent.mkdir(parents=True, exist_ok=True)

    contents = await file.read()
    storage_path.write_bytes(contents)

    metadata_stored = False
    if is_database_configured():
        try:
            create_document_metadata(
                DocumentMetadataCreate(
                    document_id=document_id,
                    organization_id=organization_id,
                    filename=filename,
                    file_type=file_type.value,
                    storage_path=str(storage_path),
                    status=DocumentStatus.UPLOADED.value
                )
            )
            metadata_stored = True
        except Exception as exc:
            raise DocumentMetadataStorageError(
                "Document was saved locally, but metadata could not be stored."
            ) from exc

    return DocumentUploadResponse(
        document_id=document_id,
        filename=filename,
        file_type=file_type.value,
        status=DocumentStatus.UPLOADED.value,
        storage_path=str(storage_path),
        metadata_stored=metadata_stored
    )
