from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_aggregate(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["checks"]["database"] is True
    assert payload["checks"]["redis"] is True


def test_health_database(client: TestClient) -> None:
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_health_redis(client: TestClient) -> None:
    response = client.get("/health/redis")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_v1_status(client: TestClient) -> None:
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "comet-api" in body["service"]
