from __future__ import annotations

from app.routes.internal import generate_view
from app.schemas import GenerateViewRequest


def test_generate_view_returns_signed_url() -> None:
    response = generate_view(
        GenerateViewRequest(
            tenant_id="tenant_001",
            patient_id="patient_123",
            actor_id="caregiver_999",
            role="caregiver",
            view="caregiver_dashboard",
        )
    )
    assert "/v/" in response.url
    assert response.expires_in_seconds == 1800
