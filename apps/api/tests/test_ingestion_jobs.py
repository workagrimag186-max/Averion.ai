from app.db.ingestion_jobs import (
    DocumentIngestionJob,
    claim_next_ingestion_job,
    fail_ingestion_job
)


class FakeCursor:
    def __init__(self, rows: list[tuple | None]) -> None:
        self.rows = iter(rows)
        self.executions: list[tuple[str, tuple | None]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        del exc_type, exc, traceback

    def execute(self, query: str, params: tuple | None = None) -> None:
        self.executions.append((query, params))

    def fetchone(self):
        return next(self.rows)


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.fake_cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        del exc_type, exc, traceback

    def cursor(self) -> FakeCursor:
        return self.fake_cursor


def make_job(attempts: int, max_attempts: int = 3) -> DocumentIngestionJob:
    return DocumentIngestionJob(
        job_id="00000000-0000-0000-0000-000000000301",
        document_id="00000000-0000-0000-0000-000000000302",
        organization_id="00000000-0000-0000-0000-000000000303",
        filename="notes.txt",
        file_type="txt",
        storage_path="organizations/org/documents/doc/notes.txt",
        attempts=attempts,
        max_attempts=max_attempts
    )


def test_claim_expires_stale_exhausted_jobs_before_claiming(monkeypatch) -> None:
    row = (
        "00000000-0000-0000-0000-000000000301",
        "00000000-0000-0000-0000-000000000302",
        "00000000-0000-0000-0000-000000000303",
        "notes.txt",
        "txt",
        "organizations/org/documents/doc/notes.txt",
        2,
        3
    )
    cursor = FakeCursor([row])

    monkeypatch.setattr(
        "app.db.ingestion_jobs.is_database_configured",
        lambda: True
    )
    monkeypatch.setattr(
        "app.db.ingestion_jobs.psycopg.connect",
        lambda *args, **kwargs: FakeConnection(cursor)
    )

    claimed = claim_next_ingestion_job("worker-1")

    assert claimed == DocumentIngestionJob(
        job_id=row[0],
        document_id=row[1],
        organization_id=row[2],
        filename=row[3],
        file_type=row[4],
        storage_path=row[5],
        attempts=row[6],
        max_attempts=row[7]
    )
    assert "with exhausted as" in cursor.executions[0][0].lower()
    assert "attempts >= max_attempts" in cursor.executions[0][0].lower()
    assert "for update skip locked" in cursor.executions[1][0].lower()
    assert "update documents" in cursor.executions[2][0].lower()


def test_retryable_failure_requeues_job(monkeypatch) -> None:
    cursor = FakeCursor([])
    monkeypatch.setattr(
        "app.db.ingestion_jobs.is_database_configured",
        lambda: True
    )
    monkeypatch.setattr(
        "app.db.ingestion_jobs.psycopg.connect",
        lambda *args, **kwargs: FakeConnection(cursor)
    )

    terminal = fail_ingestion_job(make_job(attempts=1), "temporary failure")

    assert terminal is False
    assert cursor.executions[0][1][0] == "queued"
    assert cursor.executions[1][1][0] == "uploaded"


def test_exhausted_failure_stops_retrying(monkeypatch) -> None:
    cursor = FakeCursor([])
    monkeypatch.setattr(
        "app.db.ingestion_jobs.is_database_configured",
        lambda: True
    )
    monkeypatch.setattr(
        "app.db.ingestion_jobs.psycopg.connect",
        lambda *args, **kwargs: FakeConnection(cursor)
    )

    terminal = fail_ingestion_job(make_job(attempts=3), "terminal failure")

    assert terminal is True
    assert cursor.executions[0][1][0] == "failed"
    assert cursor.executions[1][1][0] == "failed"
