"""Run all tests from the repo root:  docker compose exec api pytest"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_reports_api_and_database_up():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["api"] == "ok"
    assert response.json()["database"] == "ok"
