from dataclasses import dataclass
from pathlib import Path
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import certifi

from app.core.config import settings


class DocumentStorageError(RuntimeError):
    pass


class DocumentStorageConfigurationError(DocumentStorageError):
    pass


class DocumentStorage:
    def upload(self, object_key: str, contents: bytes, content_type: str) -> None:
        raise NotImplementedError

    def download(self, object_key: str) -> bytes:
        raise NotImplementedError

    def delete(self, object_key: str) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class LocalDocumentStorage(DocumentStorage):
    root: Path

    def _path(self, object_key: str) -> Path:
        root = self.root.resolve()
        path = (root / object_key).resolve()

        if path != root and root not in path.parents:
            raise DocumentStorageError("Invalid document object key.")

        return path

    def upload(self, object_key: str, contents: bytes, content_type: str) -> None:
        del content_type
        path = self._path(object_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)

    def download(self, object_key: str) -> bytes:
        path = self._path(object_key)

        try:
            return path.read_bytes()
        except OSError as exc:
            raise DocumentStorageError("Stored document could not be downloaded.") from exc

    def delete(self, object_key: str) -> None:
        path = self._path(object_key)

        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise DocumentStorageError("Stored document could not be deleted.") from exc

        parent = path.parent
        root = self.root.resolve()

        while parent != root and root in parent.parents:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent


@dataclass(frozen=True)
class SupabaseDocumentStorage(DocumentStorage):
    project_url: str
    service_role_key: str
    bucket: str
    timeout_seconds: float = 30.0

    def _object_url(self, object_key: str) -> str:
        encoded_bucket = quote(self.bucket, safe="")
        encoded_key = quote(object_key, safe="/")
        return (
            f"{self.project_url.rstrip('/')}/storage/v1/object/"
            f"{encoded_bucket}/{encoded_key}"
        )

    def _request(
        self,
        method: str,
        object_key: str,
        data: bytes | None = None,
        content_type: str | None = None
    ) -> bytes:
        headers = {
            "Authorization": f"Bearer {self.service_role_key}",
            "apikey": self.service_role_key
        }

        if content_type:
            headers["Content-Type"] = content_type

        if method == "POST":
            headers["x-upsert"] = "false"

        request = Request(
            self._object_url(object_key),
            data=data,
            headers=headers,
            method=method
        )

        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())

            with urlopen(
                request,
                timeout=self.timeout_seconds,
                context=ssl_context
            ) as response:
                return response.read()
        except HTTPError as exc:
            if method == "DELETE" and exc.code == 404:
                return b""

            detail = exc.read().decode("utf-8", errors="replace")
            raise DocumentStorageError(
                f"Supabase Storage request failed with status {exc.code}: {detail}"
            ) from exc
        except (OSError, URLError) as exc:
            raise DocumentStorageError("Supabase Storage could not be reached.") from exc

    def upload(self, object_key: str, contents: bytes, content_type: str) -> None:
        self._request("POST", object_key, data=contents, content_type=content_type)

    def download(self, object_key: str) -> bytes:
        return self._request("GET", object_key)

    def delete(self, object_key: str) -> None:
        self._request("DELETE", object_key)


def get_document_storage() -> DocumentStorage:
    backend = settings.document_storage_backend.strip().lower()

    if backend == "local":
        return LocalDocumentStorage(Path(settings.upload_dir))

    if backend != "supabase":
        raise DocumentStorageConfigurationError(
            "DOCUMENT_STORAGE_BACKEND must be 'local' or 'supabase'."
        )

    if not settings.supabase_url:
        raise DocumentStorageConfigurationError(
            "SUPABASE_URL is required for Supabase document storage."
        )

    if not settings.supabase_service_role_key:
        raise DocumentStorageConfigurationError(
            "SUPABASE_SERVICE_ROLE_KEY is required for Supabase document storage."
        )

    return SupabaseDocumentStorage(
        project_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        bucket=settings.supabase_storage_bucket
    )
