from fastapi.testclient import TestClient

from app.db.connection import DatabaseConnectionCheck
from app.main import app


client = TestClient(app)


def test_health_check_returns_ok() -> None:
  response = client.get("/health")

  assert response.status_code == 200
  assert response.json() == {
    "status": "ok",
    "service": "averion-api",
    "version": "0.1.0"
  }


def test_root_returns_service_links() -> None:
  response = client.get("/")

  assert response.status_code == 200
  assert response.json()["message"] == "Averion.ai API"
  assert response.json()["docs_url"] == "/docs"
  assert response.json()["health_url"] == "/health"


def test_database_health_check_returns_ok_when_connected(monkeypatch) -> None:
  def fake_check_database_connection() -> DatabaseConnectionCheck:
    return DatabaseConnectionCheck(connected=True)

  monkeypatch.setattr(
    "app.api.health.check_database_connection",
    fake_check_database_connection
  )

  response = client.get("/health/database")

  assert response.status_code == 200
  assert response.json() == {
    "status": "ok",
    "database": "postgres",
    "connected": True,
    "error": None
  }


def test_database_health_check_returns_degraded_when_disconnected(monkeypatch) -> None:
  def fake_check_database_connection() -> DatabaseConnectionCheck:
    return DatabaseConnectionCheck(
      connected=False,
      error="DATABASE_URL is not configured."
    )

  monkeypatch.setattr(
    "app.api.health.check_database_connection",
    fake_check_database_connection
  )

  response = client.get("/health/database")

  assert response.status_code == 200
  assert response.json() == {
    "status": "degraded",
    "database": "postgres",
    "connected": False,
    "error": "DATABASE_URL is not configured."
  }
