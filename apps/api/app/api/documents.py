from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.auth import RequestContext, get_request_context
from app.core.organization import get_current_organization_id
from app.core.config import settings
from app.db.documents import DatabaseNotConfiguredError, delete_document, list_documents
from app.schemas.documents import (
    DocumentDeleteResponse,
    DocumentListItem,
    DocumentUploadResponse
)
from app.services.document_service import (
    DocumentChunkStorageError,
    DocumentMetadataStorageError,
    UnsupportedDocumentTypeError,
    save_uploaded_document
)

router = APIRouter(prefix="/documents", tags=["documents"])


def _delete_local_document_file(storage_path: str) -> None:
    path = Path(storage_path)

    if not path.exists():
        return

    try:
        if path.is_file():
            path.unlink()

        if path.parent.exists() and not any(path.parent.iterdir()):
            shutil.rmtree(path.parent)
    except OSError:
        # Database deletion is the source of truth; local file cleanup is best effort.
        return


@router.get("", response_model=list[DocumentListItem])
def get_documents(
    organization_id: str = Depends(get_current_organization_id)
) -> list[DocumentListItem]:
    try:
        records = list_documents(organization_id)
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc

    return [
        DocumentListItem(
            document_id=record.document_id,
            filename=record.filename,
            file_type=record.file_type,
            status=record.status,
            storage_path=record.storage_path,
            chunks_count=record.chunks_count,
            error_message=record.error_message,
            created_at=record.created_at,
            updated_at=record.updated_at
        )
        for record in records
    ]


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_document(
    file: UploadFile = File(...),
    context: RequestContext = Depends(get_request_context)
) -> DocumentUploadResponse:
    try:
        return await save_uploaded_document(
            file=file,
            upload_dir=settings.upload_dir,
            organization_id=context.organization_id,
            uploaded_by_user_id=context.user_id
        )
    except UnsupportedDocumentTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc
    except DocumentMetadataStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc
    except DocumentChunkStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
def delete_uploaded_document(
    document_id: str,
    context: RequestContext = Depends(get_request_context)
) -> DocumentDeleteResponse:
    if context.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can delete documents."
        )

    try:
        deleted_document = delete_document(
            document_id=document_id,
            organization_id=context.organization_id
        )
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        ) from exc

    if deleted_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found in your organization."
        )

    _delete_local_document_file(deleted_document.storage_path)

    return DocumentDeleteResponse(
        document_id=deleted_document.document_id,
        filename=deleted_document.filename,
        deleted=True,
        detail="Document, chunks, and embeddings were deleted."
    )
