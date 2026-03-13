from __future__ import annotations

import time

import pytest

from app.security import ExpiredViewTokenError, create_view_token, decode_view_token


def test_create_and_decode_token_round_trip() -> None:
    token = create_view_token(
        tenant_id="tenant_001",
        patient_id="patient_123",
        actor_id="caregiver_999",
        role="caregiver",
        allowed_view="caregiver_dashboard",
        authorization_version=3,
    )
    claims = decode_view_token(token)
    assert claims.patient_id == "patient_123"
    assert claims.role == "caregiver"


def test_expired_token_rejected() -> None:
    token = create_view_token(
        tenant_id="tenant_001",
        patient_id="patient_123",
        actor_id="caregiver_999",
        role="caregiver",
        allowed_view="caregiver_dashboard",
        authorization_version=3,
        expires_in_seconds=1,
    )
    time.sleep(2)
    with pytest.raises(ExpiredViewTokenError):
        decode_view_token(token)
