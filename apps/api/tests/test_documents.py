from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.core.config import settings
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

    body = response.json()

    assert response.status_code == 201
    assert body["metadata_stored"] is True
    assert body["chunks_stored"] == 1
    assert body["status"] == "ready"
    assert stored_metadata["document_id"] == body["document_id"]
    assert stored_metadata["organization_id"] == settings.default_organization_id
    assert stored_metadata["filename"] == "notes.txt"
    assert stored_metadata["file_type"] == "txt"
    assert stored_metadata["status"] == "uploaded"
    assert stored_chunks[0].document_id == body["document_id"]
    assert stored_chunks[0].chunk_index == 0
    assert stored_chunks[0].text == "Company policy notes"
    assert stored_chunks[0].token_count == 3
    assert [update[1] for update in status_updates] == ["processing", "ready"]


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
