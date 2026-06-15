from pathlib import Path

import pytest

from app.core.config import settings
from app.db.ingestion_jobs import DocumentIngestionJob
from app.services.document_ingestion import (
    DocumentChunkLimitError,
    process_ingestion_job,
    sanitize_processing_error
)
from app.services.document_storage import DocumentStorage


class FakeDocumentStorage(DocumentStorage):
    def __init__(self, contents: bytes = b"Company policy notes") -> None:
        self.contents = contents

    def upload(self, object_key: str, contents: bytes, content_type: str) -> None:
        del object_key, contents, content_type

    def download(self, object_key: str) -> bytes:
        del object_key
        return self.contents

    def delete(self, object_key: str) -> None:
        del object_key


def make_job(attempts: int = 1, max_attempts: int = 3) -> DocumentIngestionJob:
    return DocumentIngestionJob(
        job_id="00000000-0000-0000-0000-000000000201",
        document_id="00000000-0000-0000-0000-000000000202",
        organization_id="00000000-0000-0000-0000-000000000203",
        filename="notes.txt",
        file_type="txt",
        storage_path="organizations/org/documents/doc/notes.txt",
        attempts=attempts,
        max_attempts=max_attempts
    )


def test_worker_processes_document_and_cleans_temporary_file(monkeypatch) -> None:
    captured: dict[str, object] = {}
    completed = []

    def fake_ingestion(file_path: str, file_type: str, document_id: str):
        captured["temporary_path"] = file_path
        assert Path(file_path).exists()
        assert Path(file_path).read_bytes() == b"Company policy notes"
        assert file_type == "txt"
        return [
            {
                "document_id": document_id,
                "chunk_index": 0,
                "page_number": None,
                "text": "Company policy notes"
            }
        ]

    def fake_embeddings(chunks: list[dict], batch_size: int):
        captured["batch_size"] = batch_size
        chunks[0]["embedding"] = [1.0, 0.0, 0.0]
        return chunks

    monkeypatch.setattr(
        "app.services.document_ingestion.clear_document_processing_outputs",
        lambda document_id: captured.setdefault("cleared", document_id)
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.run_ingestion_pipeline",
        fake_ingestion
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.create_document_chunks",
        lambda chunks: captured.setdefault("chunk_records", chunks)
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.generate_embeddings",
        fake_embeddings
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.store_embeddings",
        lambda chunks: captured.setdefault("embedded_chunks", chunks)
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.complete_ingestion_job",
        lambda job: completed.append(job)
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.fail_ingestion_job",
        lambda job, error: pytest.fail(error)
    )

    job = make_job()
    process_ingestion_job(job, storage=FakeDocumentStorage())

    assert captured["cleared"] == job.document_id
    assert captured["batch_size"] == settings.embedding_batch_size
    assert completed == [job]
    assert not Path(str(captured["temporary_path"])).exists()

    chunk_record = captured["chunk_records"][0]
    embedded_chunk = captured["embedded_chunks"][0]
    expected_chunk_id = f"{job.document_id}:0"
    assert chunk_record.embedding_id == expected_chunk_id
    assert embedded_chunk["chunk_id"] == expected_chunk_id
    assert embedded_chunk["organization_id"] == job.organization_id


def test_worker_reprocessing_uses_stable_ids_and_clears_prior_outputs(
    monkeypatch
) -> None:
    cleared = []
    embedded_ids = []

    monkeypatch.setattr(
        "app.services.document_ingestion.clear_document_processing_outputs",
        lambda document_id: cleared.append(document_id)
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.run_ingestion_pipeline",
        lambda **kwargs: [{
            "document_id": kwargs["document_id"],
            "chunk_index": 7,
            "page_number": 2,
            "text": "Stable chunk"
        }]
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.create_document_chunks",
        lambda chunks: None
    )

    def fake_embeddings(chunks: list[dict], batch_size: int):
        del batch_size
        chunks[0]["embedding"] = [0.5]
        return chunks

    monkeypatch.setattr(
        "app.services.document_ingestion.generate_embeddings",
        fake_embeddings
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.store_embeddings",
        lambda chunks: embedded_ids.append(chunks[0]["chunk_id"])
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.complete_ingestion_job",
        lambda job: None
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.fail_ingestion_job",
        lambda job, error: pytest.fail(error)
    )

    job = make_job()
    process_ingestion_job(job, storage=FakeDocumentStorage())
    process_ingestion_job(job, storage=FakeDocumentStorage())

    assert cleared == [job.document_id, job.document_id]
    assert embedded_ids == [
        f"{job.document_id}:7",
        f"{job.document_id}:7"
    ]


@pytest.mark.parametrize(
    ("attempts", "expected_terminal"),
    [(1, False), (3, True)]
)
def test_worker_records_retryable_and_terminal_failures(
    monkeypatch,
    attempts: int,
    expected_terminal: bool
) -> None:
    failures = []

    monkeypatch.setattr(
        "app.services.document_ingestion.clear_document_processing_outputs",
        lambda document_id: None
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.run_ingestion_pipeline",
        lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError("parser unavailable")
        )
    )

    def fake_failure(job: DocumentIngestionJob, error: str) -> bool:
        failures.append((job, error))
        return job.attempts >= job.max_attempts

    monkeypatch.setattr(
        "app.services.document_ingestion.fail_ingestion_job",
        fake_failure
    )

    job = make_job(attempts=attempts)
    process_ingestion_job(job, storage=FakeDocumentStorage())

    assert failures == [(job, "parser unavailable")]
    assert (job.attempts >= job.max_attempts) is expected_terminal


def test_worker_rejects_documents_over_chunk_limit(monkeypatch) -> None:
    failures = []
    original_limit = settings.document_max_chunks
    settings.document_max_chunks = 1

    monkeypatch.setattr(
        "app.services.document_ingestion.clear_document_processing_outputs",
        lambda document_id: None
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.run_ingestion_pipeline",
        lambda **kwargs: [
            {"chunk_index": 0, "text": "First"},
            {"chunk_index": 1, "text": "Second"}
        ]
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.create_document_chunks",
        lambda chunks: pytest.fail("Oversized document stored chunks")
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.generate_embeddings",
        lambda chunks, batch_size: pytest.fail("Oversized document embedded")
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.fail_ingestion_job",
        lambda job, error: failures.append(error) or False
    )

    try:
        process_ingestion_job(make_job(), storage=FakeDocumentStorage())
    finally:
        settings.document_max_chunks = original_limit

    assert failures == [
        "Document produced 2 chunks; the limit is 1."
    ]


def test_worker_rejects_documents_without_readable_chunks(monkeypatch) -> None:
    failures = []
    monkeypatch.setattr(
        "app.services.document_ingestion.clear_document_processing_outputs",
        lambda document_id: None
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.run_ingestion_pipeline",
        lambda **kwargs: []
    )
    monkeypatch.setattr(
        "app.services.document_ingestion.fail_ingestion_job",
        lambda job, error: failures.append(error) or False
    )

    process_ingestion_job(make_job(), storage=FakeDocumentStorage())

    assert failures == [
        "No readable chunks were produced from this document."
    ]


def test_processing_errors_hide_paths_and_secrets() -> None:
    error = RuntimeError(
        "Failed at /private/tmp/customer.txt with api_key=super-secret"
    )

    sanitized = sanitize_processing_error(error)

    assert "/private/tmp/customer.txt" not in sanitized
    assert "super-secret" not in sanitized
    assert "[REDACTED]" in sanitized
    assert "[PATH]" in sanitized
