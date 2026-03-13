from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.security import create_view_token

client = TestClient(app)


def test_dashboard_renders_for_valid_token() -> None:
    token = create_view_token(
        tenant_id="tenant_001",
        patient_id="patient_123",
        actor_id="caregiver_999",
        role="caregiver",
        allowed_view="caregiver_dashboard",
    )
    response = client.get(f"/v/{token}")
    assert response.status_code == 200
    assert "Nageswara Rao" in response.text
    assert "Medication Adherence Snapshot" in response.text
