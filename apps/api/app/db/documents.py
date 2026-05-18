from dataclasses import dataclass

import psycopg

from app.core.config import settings
from app.db.connection import is_database_configured


@dataclass(frozen=True)
class DocumentMetadataCreate:
    document_id: str
    organization_id: str
    filename: str
    file_type: str
    storage_path: str
    status: str


class DatabaseNotConfiguredError(RuntimeError):
    pass


def create_document_metadata(metadata: DocumentMetadataCreate) -> None:
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            if metadata.organization_id == settings.default_organization_id:
                cursor.execute(
                    """
                    insert into organizations (id, name)
                    values (%s::uuid, %s)
                    on conflict (id) do nothing
                    """,
                    (
                        settings.default_organization_id,
                        "Development Organization"
                    )
                )

            cursor.execute(
                """
                insert into documents (
                    id,
                    organization_id,
                    filename,
                    file_type,
                    storage_path,
                    status
                )
                values (%s::uuid, %s::uuid, %s, %s, %s, %s)
                """,
                (
                    metadata.document_id,
                    metadata.organization_id,
                    metadata.filename,
                    metadata.file_type,
                    metadata.storage_path,
                    metadata.status
                )
            )
