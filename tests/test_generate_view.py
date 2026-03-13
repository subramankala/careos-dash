from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_generate_view_returns_signed_url() -> None:
    response = client.post(
        "/generate-view",
        json={
            "tenant_id": "tenant_001",
            "patient_id": "patient_123",
            "actor_id": "caregiver_999",
            "role": "caregiver",
            "view": "caregiver_dashboard",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "/v/" in payload["url"]
    assert payload["expires_in_seconds"] == 1800
