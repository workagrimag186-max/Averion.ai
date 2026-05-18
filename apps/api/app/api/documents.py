from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.schemas.documents import DocumentUploadResponse
from app.services.document_service import (
    DocumentMetadataStorageError,
    UnsupportedDocumentTypeError,
    save_uploaded_document
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    try:
        return await save_uploaded_document(
            file=file,
            upload_dir=settings.upload_dir,
            organization_id=settings.default_organization_id
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
