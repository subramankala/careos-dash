from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings
from app.models import NotificationSettings
from app.schemas import CaregiverContext
from data.mock_data import CAREGIVER_MAPPINGS, CARE_EVENTS, ESCALATIONS, MEDICATIONS, NOTIFICATION_SETTINGS, PATIENTS, TASK_CRITICALITY


def _notification_keys() -> list[str]:
    return ["due_reminders", "critical_alerts", "daily_summary", "low_adherence_alerts"]


def _normalize_channel(value: object) -> str:
    if isinstance(value, bool):
        return "whatsapp" if value else "off"
    if isinstance(value, str):
        normalized = value.strip().lower().replace("text", "whatsapp")
        if normalized in {"voice", "whatsapp", "both", "off"}:
            return normalized
        if normalized in {"", "disabled", "none"}:
            return "off"
        return "whatsapp"
    if isinstance(value, dict):
        if not bool(value.get("enabled", True)):
            return "off"
        return _normalize_channel(value.get("channel", "whatsapp"))
    return "off"


def _channel_to_preference(channel: str) -> object:
    normalized = _normalize_channel(channel)
    if normalized == "off":
        return False
    if normalized == "whatsapp":
        return True
    return {"channel": normalized}


class MockCareOSClient:
    def __init__(self) -> None:
        self.notification_settings = {key: dict(value) for key, value in NOTIFICATION_SETTINGS.items()}

    def resolve_caregiver_context(self, phone_number: str) -> CaregiverContext | None:
        normalized = str(phone_number).replace("whatsapp:", "").strip()
        normalized = normalized.replace(" ", "")
        if normalized and not normalized.startswith("+") and normalized[0].isdigit():
            normalized = f"+{normalized}"
        mapping = CAREGIVER_MAPPINGS.get(normalized)
        if mapping is None:
            return None
        return CaregiverContext.model_validate(mapping)

    def get_dashboard_snapshot(self, *, tenant_id: str, patient_id: str, actor_id: str, role: str) -> dict:
        patient = PATIENTS[patient_id]
        meds = MEDICATIONS.get(patient_id, [])
        escalations = ESCALATIONS.get(patient_id, [])
        events = CARE_EVENTS.get(patient_id, [])
        notification_settings = self.get_notification_settings(actor_id=actor_id, patient_id=patient_id)
        return {
            "patient": {
                "id": patient.id,
                "tenant_id": patient.tenant_id,
                "full_name": patient.full_name,
                "age": patient.age,
                "sex": patient.sex,
                "primary_conditions": patient.primary_conditions,
                "care_plan_name": patient.care_plan_name,
                "last_check_in_at": patient.last_check_in_at,
            },
            "medications": [
                {
                    "id": med.id,
                    "name": med.name,
                    "dosage": med.dosage,
                    "schedule_time": med.schedule_time,
                    "status": med.status,
                }
                for med in meds
            ],
            "escalations": [
                {
                    "id": esc.id,
                    "type": esc.type,
                    "severity": esc.severity,
                    "status": esc.status,
                    "created_at": esc.created_at,
                    "summary": esc.summary,
                    "title": esc.type.replace("_", " ").title(),
                }
                for esc in escalations
            ],
            "recent_events": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "title": event.title,
                    "timestamp": event.timestamp,
                    "status": event.status,
                }
                for event in sorted(events, key=lambda item: item.timestamp, reverse=True)[:10]
            ],
            "criticality_legend": [
                {
                    "task_type": item.task_type,
                    "criticality_level": item.criticality_level,
                    "caregiver_visible_label": item.caregiver_visible_label,
                }
                for item in TASK_CRITICALITY
            ],
            "viewer": {
                "tenant_id": tenant_id,
                "patient_id": patient_id,
                "actor_id": actor_id,
                "role": role,
            },
            "notification_settings": {
                "preset": notification_settings.preset,
                "channels": dict(notification_settings.channels),
                "authorization_version": notification_settings.authorization_version,
            },
        }

    def get_notification_settings(self, *, actor_id: str, patient_id: str) -> NotificationSettings:
        raw = self.notification_settings.get((actor_id, patient_id))
        if raw is None:
            raw = {
                "preset": "primary_caregiver",
                "notification_preferences": {
                    "due_reminders": True,
                    "critical_alerts": True,
                    "daily_summary": True,
                    "low_adherence_alerts": True,
                },
                "authorization_version": 1,
            }
        preferences = dict(raw.get("notification_preferences") or {})
        return NotificationSettings(
            actor_id=actor_id,
            patient_id=patient_id,
            preset=str(raw.get("preset") or "primary_caregiver"),
            channels={key: _normalize_channel(preferences.get(key, False)) for key in _notification_keys()},
            raw_preferences=preferences,
            authorization_version=int(raw.get("authorization_version", 1) or 1),
        )

    def update_notification_settings(self, *, actor_id: str, patient_id: str, channels: dict[str, str]) -> NotificationSettings:
        existing = self.get_notification_settings(actor_id=actor_id, patient_id=patient_id)
        merged_channels = dict(existing.channels)
        merged_channels.update({key: _normalize_channel(value) for key, value in channels.items() if key in _notification_keys()})
        self.notification_settings[(actor_id, patient_id)] = {
            "preset": existing.preset,
            "notification_preferences": {key: _channel_to_preference(value) for key, value in merged_channels.items()},
            "authorization_version": existing.authorization_version + 1,
        }
        return self.get_notification_settings(actor_id=actor_id, patient_id=patient_id)


class CareOSDashboardSettingsClient:
    def __init__(self, fallback: MockCareOSClient | None = None) -> None:
        self.fallback = fallback or MockCareOSClient()

    def _careos_api_enabled(self) -> bool:
        return settings.use_real_careos_api and bool(settings.careos_api_base_url.strip())

    def _request(self, *, method: str, path: str, payload: dict | None = None) -> dict:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        request = Request(
            f"{settings.careos_api_base_url.rstrip('/')}{path}",
            method=method,
            data=body,
            headers=headers,
        )
        with urlopen(request, timeout=max(float(settings.mcp_timeout_seconds), 1.0)) as response:  # noqa: S310
            response_body = response.read().decode("utf-8")
        parsed = json.loads(response_body) if response_body else {}
        if not isinstance(parsed, dict):
            raise RuntimeError("invalid careos api result")
        return parsed

    def get_notification_settings(self, *, actor_id: str, patient_id: str) -> NotificationSettings:
        if not self._careos_api_enabled():
            return self.fallback.get_notification_settings(actor_id=actor_id, patient_id=patient_id)
        try:
            result = self._request(method="GET", path=f"/internal/caregiver-links?patient_id={patient_id}")
            links = result.get("links", [])
            if not isinstance(links, list):
                raise RuntimeError("invalid caregiver links result")
            matched = next((item for item in links if str(item.get("caregiver_participant_id", "")) == actor_id), None)
            if matched is None:
                raise RuntimeError("caregiver link not found")
            preferences = dict(matched.get("notification_preferences") or {})
            return NotificationSettings(
                actor_id=actor_id,
                patient_id=patient_id,
                preset=str(matched.get("preset") or "primary_caregiver"),
                channels={key: _normalize_channel(preferences.get(key, False)) for key in _notification_keys()},
                raw_preferences=preferences,
                authorization_version=int(matched.get("authorization_version", 1) or 1),
            )
        except (HTTPError, URLError, OSError, ValueError, RuntimeError):
            return self.fallback.get_notification_settings(actor_id=actor_id, patient_id=patient_id)

    def update_notification_settings(self, *, actor_id: str, patient_id: str, channels: dict[str, str]) -> NotificationSettings:
        if not self._careos_api_enabled():
            return self.fallback.update_notification_settings(actor_id=actor_id, patient_id=patient_id, channels=channels)
        existing = self.get_notification_settings(actor_id=actor_id, patient_id=patient_id)
        merged_channels = dict(existing.channels)
        merged_channels.update({key: _normalize_channel(value) for key, value in channels.items() if key in _notification_keys()})
        payload = {
            "actor_id": actor_id,
            "patient_id": patient_id,
            "caregiver_participant_id": actor_id,
            "notification_preferences": {key: _channel_to_preference(value) for key, value in merged_channels.items()},
        }
        try:
            result = self._request(method="POST", path="/internal/caregiver-links/notification-preferences", payload=payload)
            preferences = dict(result.get("notification_preferences") or {})
            return NotificationSettings(
                actor_id=actor_id,
                patient_id=patient_id,
                preset=str(result.get("preset") or existing.preset),
                channels={key: _normalize_channel(preferences.get(key, False)) for key in _notification_keys()},
                raw_preferences=preferences,
                authorization_version=int(result.get("authorization_version", existing.authorization_version) or existing.authorization_version),
            )
        except (HTTPError, URLError, OSError, ValueError, RuntimeError):
            return self.fallback.update_notification_settings(actor_id=actor_id, patient_id=patient_id, channels=channels)
