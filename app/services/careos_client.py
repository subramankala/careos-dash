from __future__ import annotations

from app.schemas import CaregiverContext
from data.mock_data import CAREGIVER_MAPPINGS, CARE_EVENTS, ESCALATIONS, MEDICATIONS, PATIENTS, TASK_CRITICALITY


class MockCareOSClient:
    def resolve_caregiver_context(self, phone_number: str) -> CaregiverContext | None:
        normalized = phone_number.replace("whatsapp:", "").strip()
        mapping = CAREGIVER_MAPPINGS.get(normalized)
        if mapping is None:
            return None
        return CaregiverContext.model_validate(mapping)

    def get_dashboard_snapshot(self, *, tenant_id: str, patient_id: str, actor_id: str, role: str) -> dict:
        patient = PATIENTS[patient_id]
        meds = MEDICATIONS.get(patient_id, [])
        escalations = ESCALATIONS.get(patient_id, [])
        events = CARE_EVENTS.get(patient_id, [])
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
        }
