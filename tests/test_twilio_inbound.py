from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_twilio_inbound_normalizes_plus_prefixed_sender() -> None:
    response = client.post(
        "/twilio/inbound",
        data={
            "From": " 14085157095",
            "To": "+14155238886",
            "Body": "show caregiver dashboard",
            "MessageSid": "SM_dash_001",
        },
    )
    assert response.status_code == 200
    assert "Open caregiver dashboard:" in response.text
