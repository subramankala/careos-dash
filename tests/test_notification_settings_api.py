from __future__ import annotations

import json

from app.routes.views import get_notification_settings, update_notification_settings
from app.schemas import NotificationSettingsUpdateRequest
from app.security import create_view_token


def test_notification_settings_api_returns_dashboard_scoped_settings() -> None:
    token = create_view_token(
        tenant_id="tenant_001",
        patient_id="patient_123",
        actor_id="caregiver_999",
        role="caregiver",
        allowed_view="caregiver_dashboard",
    )

    response = get_notification_settings(token)

    assert response.status_code == 200
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["actor_id"] == "caregiver_999"
    assert payload["patient_id"] == "patient_123"
    assert payload["channels"]["critical_alerts"] == "both"
    assert payload["channels"]["due_reminders"] == "whatsapp"


def test_notification_settings_api_updates_channel_preferences() -> None:
    token = create_view_token(
        tenant_id="tenant_001",
        patient_id="patient_123",
        actor_id="caregiver_999",
        role="caregiver",
        allowed_view="caregiver_dashboard",
    )

    response = update_notification_settings(
        token,
        NotificationSettingsUpdateRequest(
            channels={
                "due_reminders": "voice",
                "critical_alerts": "both",
                "daily_summary": "off",
            }
        ),
    )

    assert response.status_code == 200
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["channels"]["due_reminders"] == "voice"
    assert payload["channels"]["critical_alerts"] == "both"
    assert payload["channels"]["daily_summary"] == "off"
