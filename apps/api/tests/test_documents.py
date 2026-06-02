from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.core.auth import RequestContext, get_request_context
from app.core.config import settings
from app.db.documents import DatabaseNotConfiguredError, DocumentListRecord
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def disable_database_metadata_storage(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.document_service.is_database_configured",
        lambda: False
    )


def test_upload_document_accepts_txt_file(tmp_path: Path) -> None:
    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(tmp_path)

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("notes.txt", b"Company policy notes", "text/plain")}
        )
    finally:
        settings.upload_dir = original_upload_dir

    body = response.json()

    assert response.status_code == 201
    assert body["filename"] == "notes.txt"
    assert body["file_type"] == "txt"
    assert body["status"] == "uploaded"
    assert body["document_id"]
    assert body["metadata_stored"] is False
    assert Path(body["storage_path"]).exists()


def test_upload_document_accepts_pdf_file(tmp_path: Path) -> None:
    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(tmp_path)

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("handbook.pdf", b"%PDF-1.4", "application/pdf")}
        )
    finally:
        settings.upload_dir = original_upload_dir

    body = response.json()

    assert response.status_code == 201
    assert body["filename"] == "handbook.pdf"
    assert body["file_type"] == "pdf"
    assert body["status"] == "uploaded"


def test_upload_document_accepts_docx_file(tmp_path: Path) -> None:
    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(tmp_path)

    try:
        response = client.post(
            "/documents/upload",
            files={
                "file": (
                    "guide.docx",
                    b"docx placeholder",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            }
        )
    finally:
        settings.upload_dir = original_upload_dir

    body = response.json()

    assert response.status_code == 201
    assert body["filename"] == "guide.docx"
    assert body["file_type"] == "docx"
    assert body["status"] == "uploaded"


def test_upload_document_rejects_unsupported_file_type(tmp_path: Path) -> None:
    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(tmp_path)

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("image.png", b"not allowed", "image/png")}
        )
    finally:
        settings.upload_dir = original_upload_dir

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Unsupported file type. Upload a PDF, TXT, or DOCX file."
    }


def test_upload_document_allows_local_frontend_origin() -> None:
    response = client.options(
        "/documents/upload",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        }
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_list_documents_returns_database_documents(monkeypatch) -> None:
    def fake_list_documents(organization_id: str) -> list[DocumentListRecord]:
        assert organization_id == settings.default_organization_id

        return [
            DocumentListRecord(
                document_id="00000000-0000-0000-0000-000000000101",
                filename="handbook.pdf",
                file_type="pdf",
                status="ready",
                storage_path="uploads/doc/handbook.pdf",
                chunks_count=4,
                error_message=None,
                created_at="2026-05-18 10:00:00+00",
                updated_at="2026-05-18 10:01:00+00"
            )
        ]

    monkeypatch.setattr("app.api.documents.list_documents", fake_list_documents)

    response = client.get("/documents")

    assert response.status_code == 200
    assert response.json() == [
        {
            "document_id": "00000000-0000-0000-0000-000000000101",
            "filename": "handbook.pdf",
            "file_type": "pdf",
            "status": "ready",
            "storage_path": "uploads/doc/handbook.pdf",
            "chunks_count": 4,
            "error_message": None,
            "created_at": "2026-05-18 10:00:00+00",
            "updated_at": "2026-05-18 10:01:00+00"
        }
    ]


def test_list_documents_uses_authenticated_organization_scope(monkeypatch) -> None:
    captured_scope = {}

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id="00000000-0000-0000-0000-000000000777",
            user_id="00000000-0000-0000-0000-000000000901",
            auth_user_id="00000000-0000-0000-0000-000000000902",
            email="teammate@example.com",
            role="member",
            is_authenticated=True
        )

    def fake_list_documents(organization_id: str) -> list[DocumentListRecord]:
        captured_scope["organization_id"] = organization_id
        return []

    monkeypatch.setattr("app.api.documents.list_documents", fake_list_documents)
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.get("/documents")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []
    assert captured_scope["organization_id"] == "00000000-0000-0000-0000-000000000777"


def test_list_documents_returns_503_when_database_is_not_configured(monkeypatch) -> None:
    def fake_list_documents(organization_id: str) -> list[DocumentListRecord]:
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    monkeypatch.setattr("app.api.documents.list_documents", fake_list_documents)

    response = client.get("/documents")

    assert response.status_code == 503
    assert response.json() == {"detail": "DATABASE_URL is not configured."}


def test_upload_document_stores_metadata_when_database_is_configured(
    tmp_path: Path,
    monkeypatch
) -> None:
    stored_metadata = {}
    stored_chunks = []
    status_updates = []

    def fake_create_document_metadata(metadata) -> None:
        stored_metadata["document_id"] = metadata.document_id
        stored_metadata["organization_id"] = metadata.organization_id
        stored_metadata["uploaded_by_user_id"] = metadata.uploaded_by_user_id
        stored_metadata["filename"] = metadata.filename
        stored_metadata["file_type"] = metadata.file_type
        stored_metadata["status"] = metadata.status

    def fake_run_ingestion_pipeline(file_path, file_type, document_id):
        return [
            {
                "document_id": document_id,
                "chunk_index": 0,
                "page_number": None,
                "text": "Company policy notes"
            }
        ]

    def fake_create_document_chunks(chunks) -> int:
        stored_chunks.extend(chunks)
        return len(chunks)

    def fake_update_document_status(document_id, status, error_message=None) -> None:
        status_updates.append((document_id, status, error_message))

    def fake_generate_embeddings(chunks):
        for chunk in chunks:
            chunk["embedding"] = [1.0, 0.0, 0.0]
        return chunks

    monkeypatch.setattr(
        "app.services.document_service.is_database_configured",
        lambda: True
    )
    monkeypatch.setattr(
        "app.services.document_service.create_document_metadata",
        fake_create_document_metadata
    )
    monkeypatch.setattr(
        "app.services.document_service.run_ingestion_pipeline",
        fake_run_ingestion_pipeline
    )
    monkeypatch.setattr(
        "app.services.document_service.create_document_chunks",
        fake_create_document_chunks
    )
    monkeypatch.setattr(
        "app.services.document_service.update_document_status",
        fake_update_document_status
    )
    monkeypatch.setattr(
        "app.services.document_service.generate_embeddings",
        fake_generate_embeddings
    )
    monkeypatch.setattr(
        "app.services.document_service.store_embeddings",
        lambda chunks: None
    )

    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(tmp_path)

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("notes.txt", b"Company policy notes", "text/plain")}
        )
    finally:
        settings.upload_dir = original_upload_dir

    body = response.json()

    assert response.status_code == 201
    assert body["metadata_stored"] is True
    assert body["chunks_stored"] == 1
    assert body["status"] == "ready"
    assert stored_metadata["document_id"] == body["document_id"]
    assert stored_metadata["organization_id"] == settings.default_organization_id
    assert stored_metadata["uploaded_by_user_id"] is None
    assert stored_metadata["filename"] == "notes.txt"
    assert stored_metadata["file_type"] == "txt"
    assert stored_metadata["status"] == "uploaded"
    assert stored_chunks[0].document_id == body["document_id"]
    assert stored_chunks[0].chunk_index == 0
    assert stored_chunks[0].text == "Company policy notes"
    assert stored_chunks[0].token_count == 3
    assert stored_chunks[0].embedding_id == f"{body['document_id']}:0"
    assert [update[1] for update in status_updates] == ["processing", "ready"]


def test_upload_document_stores_authenticated_user_id(
    tmp_path: Path,
    monkeypatch
) -> None:
    stored_metadata = {}

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id=settings.default_organization_id,
            user_id="00000000-0000-0000-0000-000000000901",
            auth_user_id="00000000-0000-0000-0000-000000000902",
            email="teammate@example.com",
            role="member",
            is_authenticated=True
        )

    def fake_create_document_metadata(metadata) -> None:
        stored_metadata["organization_id"] = metadata.organization_id
        stored_metadata["uploaded_by_user_id"] = metadata.uploaded_by_user_id

    monkeypatch.setattr(
        "app.services.document_service.is_database_configured",
        lambda: True
    )
    monkeypatch.setattr(
        "app.services.document_service.create_document_metadata",
        fake_create_document_metadata
    )
    monkeypatch.setattr(
        "app.services.document_service.run_ingestion_pipeline",
        lambda file_path, file_type, document_id: [
            {
                "document_id": document_id,
                "chunk_index": 0,
                "page_number": None,
                "text": "Company policy notes"
            }
        ]
    )
    monkeypatch.setattr(
        "app.services.document_service.create_document_chunks",
        lambda chunks: len(chunks)
    )
    monkeypatch.setattr(
        "app.services.document_service.generate_embeddings",
        lambda chunks: chunks
    )
    monkeypatch.setattr(
        "app.services.document_service.store_embeddings",
        lambda chunks: None
    )
    monkeypatch.setattr(
        "app.services.document_service.update_document_status",
        lambda document_id, status, error_message=None: None
    )

    app.dependency_overrides[get_request_context] = fake_context
    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(tmp_path)

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("notes.txt", b"Company policy notes", "text/plain")}
        )
    finally:
        settings.upload_dir = original_upload_dir
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert stored_metadata["organization_id"] == settings.default_organization_id
    assert stored_metadata["uploaded_by_user_id"] == "00000000-0000-0000-0000-000000000901"


def test_upload_document_returns_503_when_metadata_storage_fails(
    tmp_path: Path,
    monkeypatch
) -> None:
    def fake_create_document_metadata(metadata) -> None:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        "app.services.document_service.is_database_configured",
        lambda: True
    )
    monkeypatch.setattr(
        "app.services.document_service.create_document_metadata",
        fake_create_document_metadata
    )

    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(tmp_path)

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("notes.txt", b"Company policy notes", "text/plain")}
        )
    finally:
        settings.upload_dir = original_upload_dir

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Document was saved locally, but metadata could not be stored."
    }


def test_upload_document_returns_503_when_chunk_storage_fails(
    tmp_path: Path,
    monkeypatch
) -> None:
    status_updates = []

    def fake_create_document_metadata(metadata) -> None:
        return None

    def fake_run_ingestion_pipeline(file_path, file_type, document_id):
        return [
            {
                "document_id": document_id,
                "chunk_index": 0,
                "page_number": None,
                "text": "Company policy notes"
            }
        ]

    def fake_create_document_chunks(chunks) -> int:
        raise RuntimeError("chunk insert failed")

    def fake_update_document_status(document_id, status, error_message=None) -> None:
        status_updates.append((document_id, status, error_message))

    monkeypatch.setattr(
        "app.services.document_service.is_database_configured",
        lambda: True
    )
    monkeypatch.setattr(
        "app.services.document_service.create_document_metadata",
        fake_create_document_metadata
    )
    monkeypatch.setattr(
        "app.services.document_service.run_ingestion_pipeline",
        fake_run_ingestion_pipeline
    )
    monkeypatch.setattr(
        "app.services.document_service.create_document_chunks",
        fake_create_document_chunks
    )
    monkeypatch.setattr(
        "app.services.document_service.update_document_status",
        fake_update_document_status
    )

    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(tmp_path)

    try:
        response = client.post(
            "/documents/upload",
            files={"file": ("notes.txt", b"Company policy notes", "text/plain")}
        )
    finally:
        settings.upload_dir = original_upload_dir

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Document metadata was stored, but chunks could not be stored."
    }
    assert [update[1] for update in status_updates] == ["processing", "failed"]
