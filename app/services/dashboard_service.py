from __future__ import annotations

from app.logging import get_logger, log_event
from app.schemas import AuthorizationContext, DashboardSummary
from app.services.careos_client import CareOSMCPClient


class DashboardService:
    def __init__(self, careos_client: CareOSMCPClient) -> None:
        self.careos_client = careos_client
        self.logger = get_logger("dashboard_service")

    def build_caregiver_dashboard(
        self,
        *,
        auth_context: AuthorizationContext,
    ) -> DashboardSummary:
        patient = self.careos_client.get_patient(
            patient_id=auth_context.patient_id,
            tenant_id=auth_context.tenant_id,
        )
        meds = self.careos_client.list_medications(patient_id=auth_context.patient_id)
        escalations = self.careos_client.list_escalations(patient_id=auth_context.patient_id)
        events = self.careos_client.list_recent_events(patient_id=auth_context.patient_id, limit=10)
        criticality = self.careos_client.list_task_criticality(patient_id=auth_context.patient_id)
        section_visibility = {
            "medications": "view_medications" in auth_context.scopes,
            "escalations": "view_escalations" in auth_context.scopes,
            "recent_events": "view_recent_events" in auth_context.scopes,
            "criticality_legend": "view_criticality" in auth_context.scopes,
        }
        snapshot = {
            "patient": {
                "id": patient.id,
                "tenant_id": patient.tenant_id,
                "full_name": patient.full_name,
                "age": patient.age,
                "sex": patient.sex,
                "primary_conditions": patient.primary_conditions,
                "care_plan_name": patient.care_plan_name,
                "last_check_in_at": patient.last_check_in_at,
                "timezone": patient.timezone,
                "primary_language": patient.primary_language,
                "persona_type": patient.persona_type,
                "risk_level": patient.risk_level,
                "status": patient.status,
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
            ]
            if section_visibility["medications"]
            else [],
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
            ]
            if section_visibility["escalations"]
            else [],
            "recent_events": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "title": event.title,
                    "timestamp": event.timestamp,
                    "status": event.status,
                }
                for event in events
            ]
            if section_visibility["recent_events"]
            else [],
            "criticality_legend": [
                {
                    "task_type": item.task_type,
                    "criticality_level": item.criticality_level,
                    "caregiver_visible_label": item.caregiver_visible_label,
                }
                for item in criticality
            ]
            if section_visibility["criticality_legend"]
            else [],
            "viewer": {
                "tenant_id": auth_context.tenant_id,
                "patient_id": auth_context.patient_id,
                "actor_id": auth_context.actor_id,
                "role": auth_context.role,
                "scopes": auth_context.scopes,
                "authorization_version": auth_context.authorization_version,
            },
            "section_visibility": section_visibility,
        }
        meds = snapshot["medications"]
        taken = sum(1 for med in meds if med["status"] == "taken")
        missed = sum(1 for med in meds if med["status"] == "missed")
        pending = sum(1 for med in meds if med["status"] == "pending")
        adherence = {
            "taken": taken,
            "missed": missed,
            "pending": pending,
            "total": len(meds),
            "completion_percent": int((taken / len(meds)) * 100) if meds else 0,
        }
        snapshot["adherence"] = adherence
        log_event(
            self.logger,
            "dashboard_snapshot_built",
            actor_id=auth_context.actor_id,
            patient_id=auth_context.patient_id,
            tenant_id=auth_context.tenant_id,
            scopes=auth_context.scopes,
            section_visibility=section_visibility,
        )
        return DashboardSummary.model_validate(snapshot)
