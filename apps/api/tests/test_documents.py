from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from fastapi.testclient import TestClient
import pytest

from app.core.auth import RequestContext, get_request_context
from app.core.config import settings
from app.db.documents import (
    DatabaseNotConfiguredError,
    DeletedDocumentRecord,
    DocumentListRecord
)
from app.main import app
from app.services.document_storage import DocumentStorage, DocumentStorageError


client = TestClient(app)


class FakeDocumentStorage(DocumentStorage):
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deleted_keys: list[str] = []

    def upload(self, object_key: str, contents: bytes, content_type: str) -> None:
        del content_type
        self.objects[object_key] = contents

    def download(self, object_key: str) -> bytes:
        return self.objects[object_key]

    def delete(self, object_key: str) -> None:
        self.deleted_keys.append(object_key)
        self.objects.pop(object_key, None)


def build_docx_bytes() -> bytes:
    output = BytesIO()

    with ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr(
            "word/document.xml",
            "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main' />"
        )

    return output.getvalue()


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
    assert body["storage_path"].startswith(
        f"organizations/{settings.default_organization_id}/documents/"
    )
    assert (tmp_path / body["storage_path"]).exists()


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
                    build_docx_bytes(),
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

    assert response.status_code == 415
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

    def fake_create_document_and_job(metadata) -> str:
        stored_metadata["document_id"] = metadata.document_id
        stored_metadata["organization_id"] = metadata.organization_id
        stored_metadata["uploaded_by_user_id"] = metadata.uploaded_by_user_id
        stored_metadata["filename"] = metadata.filename
        stored_metadata["file_type"] = metadata.file_type
        stored_metadata["storage_path"] = metadata.storage_path
        stored_metadata["status"] = metadata.status
        return "00000000-0000-0000-0000-000000000199"

    monkeypatch.setattr(
        "app.services.document_service.is_database_configured",
        lambda: True
    )
    monkeypatch.setattr(
        "app.services.document_service.create_document_and_job",
        fake_create_document_and_job
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
    assert body["chunks_stored"] == 0
    assert body["status"] == "uploaded"
    assert stored_metadata["document_id"] == body["document_id"]
    assert stored_metadata["organization_id"] == settings.default_organization_id
    assert stored_metadata["uploaded_by_user_id"] is None
    assert stored_metadata["filename"] == "notes.txt"
    assert stored_metadata["file_type"] == "txt"
    assert stored_metadata["storage_path"] == (
        f"organizations/{settings.default_organization_id}/documents/"
        f"{body['document_id']}/notes.txt"
    )
    assert stored_metadata["status"] == "uploaded"
    assert (tmp_path / stored_metadata["storage_path"]).exists()


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

    def fake_create_document_and_job(metadata) -> str:
        stored_metadata["organization_id"] = metadata.organization_id
        stored_metadata["uploaded_by_user_id"] = metadata.uploaded_by_user_id
        return "00000000-0000-0000-0000-000000000199"

    monkeypatch.setattr(
        "app.services.document_service.is_database_configured",
        lambda: True
    )
    monkeypatch.setattr(
        "app.services.document_service.create_document_and_job",
        fake_create_document_and_job
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
    def fake_create_document_and_job(metadata) -> str:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        "app.services.document_service.is_database_configured",
        lambda: True
    )
    monkeypatch.setattr(
        "app.services.document_service.create_document_and_job",
        fake_create_document_and_job
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
        "detail": (
            "Document metadata and ingestion job could not be queued; "
            "the uploaded object was removed."
        )
    }
    assert list(tmp_path.rglob("notes.txt")) == []


def test_delete_document_requires_owner_role() -> None:
    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id="00000000-0000-0000-0000-000000000777",
            user_id="00000000-0000-0000-0000-000000000901",
            auth_user_id="00000000-0000-0000-0000-000000000902",
            email="teammate@example.com",
            role="member",
            is_authenticated=True
        )

    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.delete("/documents/00000000-0000-0000-0000-000000000101")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Only organization owners can delete documents."
    }


def test_delete_document_deletes_owner_organization_document(monkeypatch) -> None:
    captured_scope = {}
    storage = FakeDocumentStorage()
    object_key = (
        "organizations/00000000-0000-0000-0000-000000000777/"
        "documents/00000000-0000-0000-0000-000000000101/handbook.pdf"
    )
    storage.objects[object_key] = b"%PDF-1.4"

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id="00000000-0000-0000-0000-000000000777",
            user_id="00000000-0000-0000-0000-000000000901",
            auth_user_id="00000000-0000-0000-0000-000000000902",
            email="owner@example.com",
            role="owner",
            is_authenticated=True
        )

    def fake_delete_document(document_id: str, organization_id: str):
        captured_scope["document_id"] = document_id
        captured_scope["organization_id"] = organization_id
        return DeletedDocumentRecord(
            document_id=document_id,
            filename="handbook.pdf",
            storage_path=object_key
        )

    monkeypatch.setattr(
        "app.api.documents.get_document_for_organization",
        fake_delete_document
    )
    monkeypatch.setattr("app.api.documents.delete_document", fake_delete_document)
    monkeypatch.setattr("app.api.documents.get_document_storage", lambda: storage)
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.delete("/documents/00000000-0000-0000-0000-000000000101")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "document_id": "00000000-0000-0000-0000-000000000101",
        "filename": "handbook.pdf",
        "deleted": True,
        "detail": "Document, chunks, and embeddings were deleted."
    }
    assert captured_scope == {
        "document_id": "00000000-0000-0000-0000-000000000101",
        "organization_id": "00000000-0000-0000-0000-000000000777"
    }
    assert storage.deleted_keys == [object_key]
    assert object_key not in storage.objects


def test_delete_document_returns_404_for_other_organization_document(monkeypatch) -> None:
    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id="00000000-0000-0000-0000-000000000777",
            user_id="00000000-0000-0000-0000-000000000901",
            auth_user_id="00000000-0000-0000-0000-000000000902",
            email="owner@example.com",
            role="owner",
            is_authenticated=True
        )

    monkeypatch.setattr(
        "app.api.documents.get_document_for_organization",
        lambda document_id, organization_id: None
    )
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.delete("/documents/00000000-0000-0000-0000-000000000101")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Document was not found in your organization."
    }


@pytest.mark.parametrize(
    ("filename", "contents", "content_type", "status_code", "detail"),
    [
        (
            "empty.txt",
            b"",
            "text/plain",
            422,
            "The uploaded document is empty."
        ),
        (
            "fake.pdf",
            b"plain text",
            "application/pdf",
            415,
            "The uploaded file content does not match its PDF extension."
        ),
        (
            "binary.txt",
            b"hello\x00world",
            "text/plain",
            415,
            "The uploaded file content does not appear to be plain text."
        ),
        (
            "notes.txt",
            b"plain text",
            "application/pdf",
            415,
            "The declared MIME type does not match a TXT file."
        ),
        (
            "../notes.txt",
            b"plain text",
            "text/plain",
            400,
            "The uploaded filename is invalid."
        )
    ]
)
def test_upload_document_rejects_invalid_payloads(
    filename: str,
    contents: bytes,
    content_type: str,
    status_code: int,
    detail: str
) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": (filename, contents, content_type)}
    )

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}


def test_upload_document_rejects_oversized_file(monkeypatch) -> None:
    monkeypatch.setattr(settings, "max_document_size_bytes", 4)

    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"12345", "text/plain")}
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": "The uploaded document exceeds the 4 byte limit."
    }


def test_upload_document_returns_503_when_object_storage_fails(monkeypatch) -> None:
    class FailingStorage(FakeDocumentStorage):
        def upload(
            self,
            object_key: str,
            contents: bytes,
            content_type: str
        ) -> None:
            raise DocumentStorageError("Object storage unavailable.")

    monkeypatch.setattr(
        "app.services.document_service.get_document_storage",
        lambda: FailingStorage()
    )

    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"Company policy notes", "text/plain")}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Object storage unavailable."}


def test_delete_document_stops_when_object_delete_fails(monkeypatch) -> None:
    deleted_from_database = []
    stored_document = DeletedDocumentRecord(
        document_id="00000000-0000-0000-0000-000000000101",
        filename="handbook.pdf",
        storage_path=(
            "organizations/00000000-0000-0000-0000-000000000777/"
            "documents/00000000-0000-0000-0000-000000000101/handbook.pdf"
        )
    )

    class FailingStorage(FakeDocumentStorage):
        def delete(self, object_key: str) -> None:
            raise DocumentStorageError("delete failed")

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id="00000000-0000-0000-0000-000000000777",
            user_id="00000000-0000-0000-0000-000000000901",
            auth_user_id="00000000-0000-0000-0000-000000000902",
            email="owner@example.com",
            role="owner",
            is_authenticated=True
        )

    monkeypatch.setattr(
        "app.api.documents.get_document_for_organization",
        lambda document_id, organization_id: stored_document
    )
    monkeypatch.setattr(
        "app.api.documents.delete_document",
        lambda document_id, organization_id: deleted_from_database.append(document_id)
    )
    monkeypatch.setattr(
        "app.api.documents.get_document_storage",
        lambda: FailingStorage()
    )
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.delete(
            "/documents/00000000-0000-0000-0000-000000000101"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": "The document object could not be deleted."
    }
    assert deleted_from_database == []


def test_retry_document_requires_owner_role() -> None:
    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id="00000000-0000-0000-0000-000000000777",
            user_id="00000000-0000-0000-0000-000000000901",
            auth_user_id="00000000-0000-0000-0000-000000000902",
            email="member@example.com",
            role="member",
            is_authenticated=True
        )

    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.post(
            "/documents/00000000-0000-0000-0000-000000000101/retry"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Only organization owners can retry failed documents."
    }


def test_retry_document_queues_failed_document_for_owner(monkeypatch) -> None:
    captured = {}

    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id="00000000-0000-0000-0000-000000000777",
            user_id="00000000-0000-0000-0000-000000000901",
            auth_user_id="00000000-0000-0000-0000-000000000902",
            email="owner@example.com",
            role="owner",
            is_authenticated=True
        )

    def fake_retry(document_id: str, organization_id: str) -> bool:
        captured["document_id"] = document_id
        captured["organization_id"] = organization_id
        return True

    monkeypatch.setattr(
        "app.api.documents.retry_failed_ingestion_job",
        fake_retry
    )
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.post(
            "/documents/00000000-0000-0000-0000-000000000101/retry"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "document_id": "00000000-0000-0000-0000-000000000101",
        "status": "uploaded",
        "detail": "Document ingestion was queued for retry."
    }
    assert captured == {
        "document_id": "00000000-0000-0000-0000-000000000101",
        "organization_id": "00000000-0000-0000-0000-000000000777"
    }


def test_retry_document_rejects_non_failed_document(monkeypatch) -> None:
    def fake_context() -> RequestContext:
        return RequestContext(
            organization_id="00000000-0000-0000-0000-000000000777",
            user_id="00000000-0000-0000-0000-000000000901",
            auth_user_id="00000000-0000-0000-0000-000000000902",
            email="owner@example.com",
            role="owner",
            is_authenticated=True
        )

    monkeypatch.setattr(
        "app.api.documents.retry_failed_ingestion_job",
        lambda document_id, organization_id: False
    )
    app.dependency_overrides[get_request_context] = fake_context

    try:
        response = client.post(
            "/documents/00000000-0000-0000-0000-000000000101/retry"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Only failed documents in your organization can be retried."
    }
