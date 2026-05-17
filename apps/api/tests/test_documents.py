from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


client = TestClient(app)


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
