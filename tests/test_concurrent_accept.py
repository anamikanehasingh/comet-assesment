from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


def _dev_token(client: TestClient, subject: uuid.UUID, role: str) -> str:
    r = client.post("/api/v1/auth/token", json={"subject": str(subject), "role": role})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_double_accept_second_fails(client: TestClient) -> None:
    rider_id = uuid.uuid4()
    driver_id = uuid.uuid4()
    tok_d = _dev_token(client, driver_id, "driver")
    tok_r = _dev_token(client, rider_id, "rider")
    h_driver = {"Authorization": f"Bearer {tok_d}"}
    h_rider = {"Authorization": f"Bearer {tok_r}"}

    client.post(
        f"/api/v1/drivers/{driver_id}/availability",
        json={"status": "online"},
        headers=h_driver,
    )
    client.post(
        f"/api/v1/drivers/{driver_id}/location",
        json={"lat": 40.73, "lng": -73.99},
        headers=h_driver,
    )
    ride_body = {
        "pickup": {"lat": 40.73, "lng": -73.99},
        "destination": {"lat": 40.78, "lng": -73.96},
        "tier": "standard",
    }
    r = client.post("/api/v1/rides", json=ride_body, headers=h_rider)
    assert r.status_code == 200, r.text
    ride_id = r.json()["ride_id"]

    pend = client.get(
        f"/api/v1/drivers/{driver_id}/offers/pending",
        headers=h_driver,
    )
    assert pend.status_code == 200, pend.text
    body = pend.json()
    assert body.get("token")
    token = body["token"]

    accept_path = f"/api/v1/drivers/{driver_id}/accept"
    payload = {"ride_id": ride_id, "token": token}
    first = client.post(accept_path, json=payload, headers=h_driver)
    second = client.post(accept_path, json=payload, headers=h_driver)
    assert first.status_code == 200
    assert second.status_code == 409
