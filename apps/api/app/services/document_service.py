from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.ai.ingestion_pipeline import run_ingestion_pipeline
from app.db.schema import DocumentFileType, DocumentStatus
from app.db.connection import is_database_configured
from app.db.documents import (
    DocumentChunkCreate,
    DocumentMetadataCreate,
    create_document_chunks,
    create_document_metadata,
    update_document_status
)
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


class DocumentChunkStorageError(RuntimeError):
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


def _estimate_token_count(text: str) -> int:
    return len(text.split())


def _build_chunk_records(chunks: list[dict], document_id: str) -> list[DocumentChunkCreate]:
    records: list[DocumentChunkCreate] = []

    for fallback_index, chunk in enumerate(chunks):
        text = str(chunk.get("text", "")).strip()
        if not text:
            continue

        records.append(
            DocumentChunkCreate(
                document_id=document_id,
                chunk_index=int(chunk.get("chunk_index", fallback_index)),
                page_number=chunk.get("page_number"),
                text=text,
                token_count=_estimate_token_count(text),
                embedding_id=chunk.get("embedding_id")
            )
        )

    return records


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
    chunks_stored = 0
    status = DocumentStatus.UPLOADED.value

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

        try:
            update_document_status(document_id, DocumentStatus.PROCESSING.value)
            chunks = run_ingestion_pipeline(
                file_path=str(storage_path),
                file_type=file_type.value,
                document_id=document_id
            )
            chunk_records = _build_chunk_records(chunks, document_id)

            if chunk_records:
                chunks_stored = create_document_chunks(chunk_records)
                status = DocumentStatus.READY.value
                update_document_status(document_id, status)
            else:
                status = DocumentStatus.FAILED.value
                update_document_status(
                    document_id,
                    status,
                    "No readable chunks were produced from this document."
                )
        except Exception as exc:
            status = DocumentStatus.FAILED.value
            try:
                update_document_status(document_id, status, str(exc))
            except Exception:
                pass

            raise DocumentChunkStorageError(
                "Document metadata was stored, but chunks could not be stored."
            ) from exc

    return DocumentUploadResponse(
        document_id=document_id,
        filename=filename,
        file_type=file_type.value,
        status=status,
        storage_path=str(storage_path),
        metadata_stored=metadata_stored,
        chunks_stored=chunks_stored
    )
