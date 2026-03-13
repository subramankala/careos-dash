from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings
from app.logging import get_logger, log_event
from app.models import AuthorizationGrant, CareEvent, Escalation, Medication, Patient, TaskCriticality
from app.schemas import CaregiverContext
from data.mock_data import AUTHORIZATION_GRANTS, CAREGIVER_MAPPINGS, CARE_EVENTS, ESCALATIONS, MEDICATIONS, PATIENTS, TASK_CRITICALITY


class MockCareOSMCPClient:
    """Mocked MCP-shaped CareOS contract for MVP development."""

    def resolve_caregiver_context(self, phone_number: str) -> CaregiverContext | None:
        normalized = str(phone_number).replace("whatsapp:", "").strip()
        normalized = normalized.replace(" ", "")
        if normalized and not normalized.startswith("+") and normalized[0].isdigit():
            normalized = f"+{normalized}"
        mapping = CAREGIVER_MAPPINGS.get(normalized)
        if mapping is None:
            return None
        return CaregiverContext.model_validate(mapping)

    def get_active_authorization_grant(
        self,
        *,
        actor_id: str,
        patient_id: str,
        tenant_id: str,
    ) -> AuthorizationGrant | None:
        for grant in AUTHORIZATION_GRANTS:
            if grant.actor_id != actor_id:
                continue
            if grant.patient_id != patient_id or grant.tenant_id != tenant_id:
                continue
            if grant.status != "active" or grant.revoked_at is not None:
                continue
            return grant
        return None

    def get_patient(self, *, patient_id: str, tenant_id: str) -> Patient:
        patient = PATIENTS[patient_id]
        if patient.tenant_id != tenant_id:
            raise ValueError("tenant-patient mismatch")
        return patient

    def list_medications(self, *, patient_id: str) -> list[Medication]:
        return list(MEDICATIONS.get(patient_id, []))

    def list_escalations(self, *, patient_id: str) -> list[Escalation]:
        return list(ESCALATIONS.get(patient_id, []))

    def list_recent_events(self, *, patient_id: str, limit: int = 10) -> list[CareEvent]:
        events = sorted(CARE_EVENTS.get(patient_id, []), key=lambda item: item.timestamp, reverse=True)
        return events[:limit]

    def list_task_criticality(self, *, patient_id: str) -> list[TaskCriticality]:
        return list(TASK_CRITICALITY)


class CareOSMCPClient:
    """Real MCP-backed CareOS client with mock fallback for local MVP work."""

    def __init__(self, fallback: MockCareOSMCPClient | None = None) -> None:
        self.fallback = fallback or MockCareOSMCPClient()
        self.logger = get_logger("careos_mcp_client")

    def _mcp_enabled(self) -> bool:
        return settings.use_real_mcp and bool(settings.mcp_base_url.strip())

    def _call_tool(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any] | list[Any]:
        if not self._mcp_enabled():
            raise RuntimeError("mcp disabled")
        last_error: Exception | None = None
        attempts = max(int(settings.mcp_retry_attempts), 1)
        for attempt in range(1, attempts + 1):
            try:
                payload = json.dumps({"tool": tool, "arguments": arguments}).encode("utf-8")
                headers = {"Content-Type": "application/json"}
                if settings.mcp_api_key.strip():
                    headers["x-mcp-api-key"] = settings.mcp_api_key.strip()
                request = Request(
                    f"{settings.mcp_base_url.rstrip('/')}/mcp/call",
                    method="POST",
                    data=payload,
                    headers=headers,
                )
                with urlopen(request, timeout=max(float(settings.mcp_timeout_seconds), 1.0)) as response:  # noqa: S310
                    body = json.loads(response.read().decode("utf-8"))
                if not body.get("ok", False):
                    raise RuntimeError(str(body.get("error", "unknown mcp error")))
                return body.get("result") or {}
            except (HTTPError, URLError, OSError, ValueError, RuntimeError) as exc:
                last_error = exc
                if attempt >= attempts:
                    break
                time.sleep(0.2 * attempt)
        raise RuntimeError(str(last_error or "unknown mcp error"))

    def _fallback_event(self, *, operation: str, reason: str, **fields: Any) -> None:
        log_event(self.logger, "careos_mcp_fallback", operation=operation, reason=reason, **fields)

    def resolve_caregiver_context(self, phone_number: str) -> CaregiverContext | None:
        if not self._mcp_enabled():
            return self.fallback.resolve_caregiver_context(phone_number)
        try:
            result = self._call_tool("careos_resolve_caregiver_context", {"phone_number": phone_number})
            if not isinstance(result, dict):
                raise RuntimeError("invalid context result")
            return CaregiverContext(
                tenant_id=str(result["tenant_id"]),
                patient_id=str(result["patient_id"]),
                actor_id=str(result["participant_id"]),
                role="caregiver",
                phone_number=str(phone_number).replace("whatsapp:", "").strip(),
            )
        except (HTTPError, URLError, OSError, ValueError, KeyError, RuntimeError) as exc:
            self._fallback_event(operation="resolve_caregiver_context", reason=str(exc), phone_number=phone_number)
            return self.fallback.resolve_caregiver_context(phone_number)

    def get_active_authorization_grant(
        self,
        *,
        actor_id: str,
        patient_id: str,
        tenant_id: str,
    ) -> AuthorizationGrant | None:
        if not self._mcp_enabled():
            return self.fallback.get_active_authorization_grant(
                actor_id=actor_id,
                patient_id=patient_id,
                tenant_id=tenant_id,
            )
        try:
            result = self._call_tool(
                "careos_get_view_access",
                {
                    "actor_id": actor_id,
                    "patient_id": patient_id,
                    "tenant_id": tenant_id,
                    "view": "caregiver_dashboard",
                },
            )
            if not isinstance(result, dict):
                raise RuntimeError("invalid authorization result")
            return AuthorizationGrant(
                authorization_id=str(result["authorization_id"]),
                tenant_id=str(result["tenant_id"]),
                patient_id=str(result["patient_id"]),
                actor_id=str(result["actor_id"]),
                actor_type=str(result.get("actor_type", "caregiver")),
                granted_by=str(result.get("granted_by", patient_id)),
                scopes=[str(scope) for scope in result.get("scopes", [])],
                status=str(result.get("status", "active")),
                effective_at=datetime.fromisoformat(str(result["effective_at"]).replace("Z", "+00:00")),
                revoked_at=(
                    datetime.fromisoformat(str(result["revoked_at"]).replace("Z", "+00:00"))
                    if result.get("revoked_at")
                    else None
                ),
                authorization_version=int(result.get("authorization_version", 1)),
            )
        except (HTTPError, URLError, OSError, ValueError, KeyError, RuntimeError) as exc:
            self._fallback_event(
                operation="get_active_authorization_grant",
                reason=str(exc),
                actor_id=actor_id,
                patient_id=patient_id,
                tenant_id=tenant_id,
            )
            return self.fallback.get_active_authorization_grant(
                actor_id=actor_id,
                patient_id=patient_id,
                tenant_id=tenant_id,
            )

    def get_patient(self, *, patient_id: str, tenant_id: str) -> Patient:
        if not self._mcp_enabled():
            return self.fallback.get_patient(patient_id=patient_id, tenant_id=tenant_id)
        try:
            result = self._call_tool("careos_get_patient_summary", {"patient_id": patient_id})
            if not isinstance(result, dict):
                raise RuntimeError("invalid patient result")
            if str(result["tenant_id"]) != tenant_id:
                raise ValueError("tenant-patient mismatch")
            last_check_in_at = result.get("last_check_in_at")
            return Patient(
                id=str(result["id"]),
                tenant_id=str(result["tenant_id"]),
                full_name=str(result.get("full_name") or result["id"]),
                age=int(result["age"]) if result.get("age") is not None else None,
                sex=str(result["sex"]) if result.get("sex") is not None else None,
                primary_conditions=[str(item) for item in result.get("primary_conditions", [])],
                care_plan_name=str(result.get("care_plan_name") or "Active care plan"),
                last_check_in_at=(
                    datetime.fromisoformat(str(last_check_in_at).replace("Z", "+00:00")) if last_check_in_at else None
                ),
                timezone=str(result.get("timezone") or "UTC"),
                primary_language=str(result.get("primary_language") or "en"),
                persona_type=str(result.get("persona_type") or "caregiver_managed_elder"),
                risk_level=str(result.get("risk_level") or "medium"),
                status=str(result.get("status") or "active"),
            )
        except (HTTPError, URLError, OSError, ValueError, KeyError, RuntimeError) as exc:
            self._fallback_event(operation="get_patient", reason=str(exc), patient_id=patient_id, tenant_id=tenant_id)
            return self.fallback.get_patient(patient_id=patient_id, tenant_id=tenant_id)

    def list_medications(self, *, patient_id: str) -> list[Medication]:
        if not self._mcp_enabled():
            return self.fallback.list_medications(patient_id=patient_id)
        try:
            result = self._call_tool("careos_get_medications", {"patient_id": patient_id})
            items = result.get("items", []) if isinstance(result, dict) else []
            return [
                Medication(
                    id=str(item["id"]),
                    patient_id=str(item.get("patient_id", patient_id)),
                    name=str(item.get("name", "")),
                    dosage=str(item.get("dosage", "")),
                    schedule_time=str(item.get("schedule_time", "")),
                    status=str(item.get("status", "pending")),
                )
                for item in items
            ]
        except (HTTPError, URLError, OSError, ValueError, KeyError, RuntimeError) as exc:
            self._fallback_event(operation="list_medications", reason=str(exc), patient_id=patient_id)
            return self.fallback.list_medications(patient_id=patient_id)

    def list_escalations(self, *, patient_id: str) -> list[Escalation]:
        if not self._mcp_enabled():
            return self.fallback.list_escalations(patient_id=patient_id)
        try:
            result = self._call_tool("careos_get_escalations", {"patient_id": patient_id})
            items = result.get("items", []) if isinstance(result, dict) else []
            return [
                Escalation(
                    id=str(item["id"]),
                    patient_id=str(item.get("patient_id", patient_id)),
                    type=str(item.get("type", "")),
                    severity=str(item.get("severity", "medium")),
                    status=str(item.get("status", "open")),
                    created_at=datetime.fromisoformat(str(item["created_at"]).replace("Z", "+00:00")),
                    summary=str(item.get("summary", "")),
                )
                for item in items
            ]
        except (HTTPError, URLError, OSError, ValueError, KeyError, RuntimeError) as exc:
            self._fallback_event(operation="list_escalations", reason=str(exc), patient_id=patient_id)
            return self.fallback.list_escalations(patient_id=patient_id)

    def list_recent_events(self, *, patient_id: str, limit: int = 10) -> list[CareEvent]:
        if not self._mcp_enabled():
            return self.fallback.list_recent_events(patient_id=patient_id, limit=limit)
        try:
            result = self._call_tool("careos_get_recent_events", {"patient_id": patient_id, "limit": limit})
            items = result.get("items", []) if isinstance(result, dict) else []
            return [
                CareEvent(
                    id=str(item["id"]),
                    patient_id=str(item.get("patient_id", patient_id)),
                    event_type=str(item.get("event_type", "")),
                    title=str(item.get("title", "")),
                    timestamp=datetime.fromisoformat(str(item["timestamp"]).replace("Z", "+00:00")),
                    status=str(item.get("status", "")),
                )
                for item in items
            ]
        except (HTTPError, URLError, OSError, ValueError, KeyError, RuntimeError) as exc:
            self._fallback_event(operation="list_recent_events", reason=str(exc), patient_id=patient_id)
            return self.fallback.list_recent_events(patient_id=patient_id, limit=limit)

    def list_task_criticality(self, *, patient_id: str) -> list[TaskCriticality]:
        if not self._mcp_enabled():
            return self.fallback.list_task_criticality(patient_id=patient_id)
        try:
            result = self._call_tool("careos_get_task_criticality", {"patient_id": patient_id})
            items = result.get("items", []) if isinstance(result, dict) else []
            return [
                TaskCriticality(
                    task_type=str(item.get("task_type", "")),
                    criticality_level=str(item.get("criticality_level", "OPTIONAL_LIFESTYLE")),
                    caregiver_visible_label=str(item.get("caregiver_visible_label", "Optional lifestyle")),
                )
                for item in items
            ]
        except (HTTPError, URLError, OSError, ValueError, KeyError, RuntimeError) as exc:
            self._fallback_event(operation="list_task_criticality", reason=str(exc), patient_id=patient_id)
            return self.fallback.list_task_criticality(patient_id=patient_id)
