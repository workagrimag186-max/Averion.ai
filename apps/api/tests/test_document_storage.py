from pathlib import Path
from urllib.request import Request

import pytest

from app.core.config import settings
from app.services import document_storage
from app.services.document_storage import (
    DocumentStorageConfigurationError,
    DocumentStorageError,
    LocalDocumentStorage,
    SupabaseDocumentStorage,
    get_document_storage
)


class FakeResponse:
    def __init__(self, contents: bytes = b"") -> None:
        self.contents = contents

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.contents


def test_local_storage_round_trip_and_delete(tmp_path: Path) -> None:
    storage = LocalDocumentStorage(tmp_path)
    object_key = "organizations/org/documents/doc/notes.txt"

    storage.upload(object_key, b"notes", "text/plain")

    assert storage.download(object_key) == b"notes"
    assert (tmp_path / object_key).read_bytes() == b"notes"

    storage.delete(object_key)

    assert not (tmp_path / object_key).exists()


def test_local_storage_rejects_path_escape(tmp_path: Path) -> None:
    storage = LocalDocumentStorage(tmp_path)

    with pytest.raises(DocumentStorageError, match="Invalid document object key"):
        storage.upload("../outside.txt", b"notes", "text/plain")


def test_supabase_storage_sends_service_role_headers(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(
        request: Request,
        timeout: float,
        context
    ) -> FakeResponse:
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["headers"] = dict(request.header_items())
        captured["data"] = request.data
        captured["timeout"] = timeout
        captured["context"] = context
        return FakeResponse()

    monkeypatch.setattr(document_storage, "urlopen", fake_urlopen)
    storage = SupabaseDocumentStorage(
        project_url="https://project.supabase.co",
        service_role_key="service-secret",
        bucket="documents"
    )

    storage.upload(
        "organizations/org/documents/doc/report 1.pdf",
        b"%PDF-1.4",
        "application/pdf"
    )

    assert captured["url"] == (
        "https://project.supabase.co/storage/v1/object/documents/"
        "organizations/org/documents/doc/report%201.pdf"
    )
    assert captured["method"] == "POST"
    assert captured["data"] == b"%PDF-1.4"
    assert captured["timeout"] == 30.0
    headers = {
        str(key).lower(): value
        for key, value in dict(captured["headers"]).items()
    }
    assert headers["authorization"] == "Bearer service-secret"
    assert headers["apikey"] == "service-secret"
    assert headers["content-type"] == "application/pdf"
    assert headers["x-upsert"] == "false"


def test_storage_factory_requires_supabase_credentials(monkeypatch) -> None:
    monkeypatch.setattr(settings, "document_storage_backend", "supabase")
    monkeypatch.setattr(settings, "supabase_url", None)
    monkeypatch.setattr(settings, "supabase_service_role_key", None)

    with pytest.raises(
        DocumentStorageConfigurationError,
        match="SUPABASE_URL is required"
    ):
        get_document_storage()


def test_storage_factory_uses_local_backend(
    tmp_path: Path,
    monkeypatch
) -> None:
    monkeypatch.setattr(settings, "document_storage_backend", "local")
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))

    storage = get_document_storage()

    assert isinstance(storage, LocalDocumentStorage)
    assert storage.root == tmp_path
