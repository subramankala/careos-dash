from __future__ import annotations

import json
from datetime import datetime

from app.config import settings
from app.services import careos_client as careos_client_module
from app.services.careos_client import CareOSMCPClient


def test_careos_mcp_client_maps_real_tool_payloads(monkeypatch) -> None:
    previous_use_real_mcp = settings.use_real_mcp
    previous_mcp_base_url = settings.mcp_base_url
    try:
        settings.use_real_mcp = True
        settings.mcp_base_url = "http://127.0.0.1:8110"
        client = CareOSMCPClient()

        def _fake_call_tool(tool: str, arguments: dict):
            if tool == "careos_get_patient_summary":
                return {
                    "id": "patient_live",
                    "tenant_id": "tenant_live",
                    "full_name": "Live Patient",
                    "age": None,
                    "sex": None,
                    "primary_conditions": [],
                    "care_plan_name": "Active care plan",
                    "last_check_in_at": None,
                    "timezone": "UTC",
                    "primary_language": "te",
                    "persona_type": "caregiver_managed_elder",
                    "risk_level": "high",
                    "status": "active",
                }
            if tool == "careos_get_view_access":
                return {
                    "authorization_id": "auth_live",
                    "tenant_id": "tenant_live",
                    "patient_id": "patient_live",
                    "actor_id": "actor_live",
                    "actor_type": "caregiver",
                    "granted_by": "patient_live",
                    "scopes": ["view_dashboard", "view_criticality"],
                    "status": "active",
                    "effective_at": datetime.now().isoformat(),
                    "revoked_at": None,
                    "authorization_version": 7,
                }
            raise AssertionError(f"unexpected tool {tool}")

        monkeypatch.setattr(client, "_call_tool", _fake_call_tool)

        patient = client.get_patient(patient_id="patient_live", tenant_id="tenant_live")
        grant = client.get_active_authorization_grant(
            actor_id="actor_live",
            patient_id="patient_live",
            tenant_id="tenant_live",
        )

        assert patient.full_name == "Live Patient"
        assert patient.timezone == "UTC"
        assert patient.primary_language == "te"
        assert patient.risk_level == "high"
        assert grant is not None
        assert grant.authorization_version == 7
        assert grant.scopes == ["view_dashboard", "view_criticality"]
    finally:
        settings.use_real_mcp = previous_use_real_mcp
        settings.mcp_base_url = previous_mcp_base_url


def test_careos_mcp_client_falls_back_to_mock_on_error(monkeypatch) -> None:
    previous_use_real_mcp = settings.use_real_mcp
    previous_mcp_base_url = settings.mcp_base_url
    try:
        settings.use_real_mcp = True
        settings.mcp_base_url = "http://127.0.0.1:8110"
        client = CareOSMCPClient()

        def _boom(tool: str, arguments: dict):
            raise RuntimeError("mcp unavailable")

        monkeypatch.setattr(client, "_call_tool", _boom)

        patient = client.get_patient(patient_id="patient_123", tenant_id="tenant_001")
        meds = client.list_medications(patient_id="patient_123")

        assert patient.full_name == "Nageswara Rao"
        assert meds
    finally:
        settings.use_real_mcp = previous_use_real_mcp
        settings.mcp_base_url = previous_mcp_base_url


def test_careos_mcp_client_retries_before_success(monkeypatch) -> None:
    previous_use_real_mcp = settings.use_real_mcp
    previous_mcp_base_url = settings.mcp_base_url
    previous_retry_attempts = settings.mcp_retry_attempts
    previous_timeout = settings.mcp_timeout_seconds
    try:
        settings.use_real_mcp = True
        settings.mcp_base_url = "http://127.0.0.1:8110"
        settings.mcp_retry_attempts = 3
        settings.mcp_timeout_seconds = 1
        client = CareOSMCPClient()
        calls = {"count": 0}

        class _Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps({"ok": True, "result": {
                    "id": "patient_live",
                    "tenant_id": "tenant_live",
                    "full_name": "Recovered Patient",
                    "age": None,
                    "sex": None,
                    "primary_conditions": [],
                    "care_plan_name": "Active care plan",
                    "last_check_in_at": None,
                    "timezone": "UTC",
                    "primary_language": "en",
                    "persona_type": "caregiver_managed_elder",
                    "risk_level": "medium",
                    "status": "active",
                }}).encode("utf-8")

        def _flaky_urlopen(request, timeout=0):
            calls["count"] += 1
            if calls["count"] < 3:
                raise RuntimeError("temporary mcp failure")
            return _Response()

        monkeypatch.setattr(careos_client_module, "urlopen", _flaky_urlopen)
        patient = client.get_patient(patient_id="patient_live", tenant_id="tenant_live")
        assert patient.full_name == "Recovered Patient"
        assert calls["count"] == 3
    finally:
        settings.use_real_mcp = previous_use_real_mcp
        settings.mcp_base_url = previous_mcp_base_url
        settings.mcp_retry_attempts = previous_retry_attempts
        settings.mcp_timeout_seconds = previous_timeout
