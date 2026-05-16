from fastapi.testclient import TestClient

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
