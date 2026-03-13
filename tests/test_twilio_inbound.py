from __future__ import annotations

from app.routes.twilio import twilio_inbound


def test_twilio_inbound_normalizes_plus_prefixed_sender() -> None:
    response = twilio_inbound(
        From=" 14085157095",
        To="+14155238886",
        Body="show caregiver dashboard",
        MessageSid="SM_dash_001",
    )
    assert response.status_code == 200
    assert b"Open caregiver dashboard:" in response.body
