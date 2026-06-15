from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterator
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from fastapi import UploadFile

from app.ai.embeddings import generate_embeddings
from app.ai.ingestion_pipeline import run_ingestion_pipeline
from app.ai.vector_store import build_chunk_id, store_embeddings
from app.core.config import settings
from app.db.connection import is_database_configured
from app.db.documents import (
    DocumentChunkCreate,
    DocumentMetadataCreate,
    create_document_chunks,
    create_document_metadata,
    delete_document,
    update_document_status
)
from app.db.schema import DocumentFileType, DocumentStatus
from app.schemas.documents import DocumentUploadResponse
from app.services.document_storage import (
    DocumentStorage,
    DocumentStorageError,
    get_document_storage
)


SUPPORTED_FILE_TYPES = {
    ".pdf": DocumentFileType.PDF,
    ".txt": DocumentFileType.TXT,
    ".docx": DocumentFileType.DOCX
}

EXPECTED_CONTENT_TYPES = {
    DocumentFileType.PDF: {"application/pdf"},
    DocumentFileType.TXT: {"text/plain"},
    DocumentFileType.DOCX: {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
}


class DocumentValidationError(ValueError):
    status_code = 400


class UnsupportedDocumentTypeError(DocumentValidationError):
    status_code = 415


class InvalidDocumentFilenameError(DocumentValidationError):
    status_code = 400


class EmptyDocumentError(DocumentValidationError):
    status_code = 422


class DocumentTooLargeError(DocumentValidationError):
    status_code = 413


class DocumentContentMismatchError(DocumentValidationError):
    status_code = 415


class DocumentMetadataStorageError(RuntimeError):
    pass


class DocumentChunkStorageError(RuntimeError):
    pass


def validate_filename(filename: str) -> str:
    normalized = filename.strip()

    if (
        not normalized
        or normalized in {".", ".."}
        or Path(normalized).name != normalized
        or "/" in normalized
        or "\\" in normalized
        or any(ord(character) < 32 for character in normalized)
    ):
        raise InvalidDocumentFilenameError("The uploaded filename is invalid.")

    if len(normalized.encode("utf-8")) > 255:
        raise InvalidDocumentFilenameError(
            "The uploaded filename must be 255 bytes or fewer."
        )

    return normalized


def get_file_type(filename: str) -> DocumentFileType:
    suffix = Path(filename).suffix.lower()

    try:
        return SUPPORTED_FILE_TYPES[suffix]
    except KeyError as exc:
        raise UnsupportedDocumentTypeError(
            "Unsupported file type. Upload a PDF, TXT, or DOCX file."
        ) from exc


def build_storage_path(
    organization_id: str,
    document_id: str,
    filename: str
) -> str:
    return (
        f"organizations/{organization_id}/documents/"
        f"{document_id}/{filename}"
    )


def _validate_declared_content_type(
    file_type: DocumentFileType,
    content_type: str | None
) -> None:
    normalized = (content_type or "").split(";", maxsplit=1)[0].strip().lower()

    if normalized not in EXPECTED_CONTENT_TYPES[file_type]:
        raise DocumentContentMismatchError(
            f"The declared MIME type does not match a {file_type.value.upper()} file."
        )


def _validate_docx(contents: bytes) -> None:
    try:
        with ZipFile(BytesIO(contents)) as archive:
            names = set(archive.namelist())
    except (BadZipFile, OSError) as exc:
        raise DocumentContentMismatchError(
            "The uploaded file is not a valid DOCX document."
        ) from exc

    if "[Content_Types].xml" not in names or "word/document.xml" not in names:
        raise DocumentContentMismatchError(
            "The uploaded file is not a valid DOCX document."
        )


def _validate_file_contents(
    file_type: DocumentFileType,
    contents: bytes
) -> None:
    if file_type == DocumentFileType.PDF and not contents.startswith(b"%PDF-"):
        raise DocumentContentMismatchError(
            "The uploaded file content does not match its PDF extension."
        )

    if file_type == DocumentFileType.DOCX:
        _validate_docx(contents)

    if file_type == DocumentFileType.TXT:
        if b"\x00" in contents:
            raise DocumentContentMismatchError(
                "The uploaded file content does not appear to be plain text."
            )

        try:
            contents.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentContentMismatchError(
                "TXT uploads must contain valid UTF-8 text."
            ) from exc


async def read_and_validate_upload(
    file: UploadFile
) -> tuple[str, DocumentFileType, bytes, str]:
    filename = validate_filename(file.filename or "")
    file_type = get_file_type(filename)
    _validate_declared_content_type(file_type, file.content_type)

    contents = await file.read(settings.max_document_size_bytes + 1)

    if not contents:
        raise EmptyDocumentError("The uploaded document is empty.")

    if len(contents) > settings.max_document_size_bytes:
        raise DocumentTooLargeError(
            f"The uploaded document exceeds the {settings.max_document_size_bytes} byte limit."
        )

    _validate_file_contents(file_type, contents)
    content_type = next(iter(EXPECTED_CONTENT_TYPES[file_type]))
    return filename, file_type, contents, content_type


@contextmanager
def temporary_document_file(
    storage: DocumentStorage,
    object_key: str,
    suffix: str
) -> Iterator[str]:
    contents = storage.download(object_key)
    temporary_path: Path | None = None

    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
            temporary_file.write(contents)
            temporary_path = Path(temporary_file.name)

        yield str(temporary_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


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


def _cleanup_failed_upload(
    storage: DocumentStorage,
    object_key: str,
    document_id: str,
    organization_id: str,
    metadata_stored: bool
) -> None:
    if metadata_stored:
        try:
            delete_document(document_id, organization_id)
        except Exception:
            pass

    try:
        storage.delete(object_key)
    except DocumentStorageError:
        pass


async def save_uploaded_document(
    file: UploadFile,
    organization_id: str,
    uploaded_by_user_id: str | None = None,
    storage: DocumentStorage | None = None
) -> DocumentUploadResponse:
    filename, file_type, contents, content_type = await read_and_validate_upload(file)
    document_id = str(uuid4())
    object_key = build_storage_path(
        organization_id,
        document_id,
        filename
    )
    document_storage = storage or get_document_storage()
    metadata_stored = False
    chunks_stored = 0
    status = DocumentStatus.UPLOADED.value

    try:
        document_storage.upload(object_key, contents, content_type)
    except DocumentStorageError:
        raise

    if is_database_configured():
        try:
            create_document_metadata(
                DocumentMetadataCreate(
                    document_id=document_id,
                    organization_id=organization_id,
                    uploaded_by_user_id=uploaded_by_user_id,
                    filename=filename,
                    file_type=file_type.value,
                    storage_path=object_key,
                    status=DocumentStatus.UPLOADED.value
                )
            )
            metadata_stored = True
        except Exception as exc:
            _cleanup_failed_upload(
                document_storage,
                object_key,
                document_id,
                organization_id,
                metadata_stored=False
            )
            raise DocumentMetadataStorageError(
                "Document metadata could not be stored; the uploaded object was removed."
            ) from exc

        try:
            update_document_status(document_id, DocumentStatus.PROCESSING.value)

            with temporary_document_file(
                document_storage,
                object_key,
                Path(filename).suffix.lower()
            ) as temporary_path:
                chunks = run_ingestion_pipeline(
                    file_path=temporary_path,
                    file_type=file_type.value,
                    document_id=document_id
                )

            for chunk in chunks:
                chunk["organization_id"] = organization_id
                chunk["chunk_id"] = build_chunk_id(
                    document_id,
                    chunk.get("chunk_index", 0)
                )
                chunk["embedding_id"] = chunk["chunk_id"]

            chunk_records = _build_chunk_records(chunks, document_id)

            if not chunk_records:
                raise RuntimeError(
                    "No readable chunks were produced from this document."
                )

            chunks_stored = create_document_chunks(chunk_records)
            chunks_with_embeddings = generate_embeddings(chunks)
            store_embeddings(chunks_with_embeddings)
            status = DocumentStatus.READY.value
            update_document_status(document_id, status)
        except Exception as exc:
            _cleanup_failed_upload(
                document_storage,
                object_key,
                document_id,
                organization_id,
                metadata_stored=True
            )
            raise DocumentChunkStorageError(
                "Document processing failed; metadata, chunks, embeddings, and the uploaded object were removed."
            ) from exc

    return DocumentUploadResponse(
        document_id=document_id,
        filename=filename,
        file_type=file_type.value,
        status=status,
        storage_path=object_key,
        metadata_stored=metadata_stored,
        chunks_stored=chunks_stored
    )
