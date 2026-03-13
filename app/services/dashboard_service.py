from __future__ import annotations

from app.schemas import DashboardSummary
from app.services.careos_client import MockCareOSClient


class DashboardService:
    def __init__(self, careos_client: MockCareOSClient) -> None:
        self.careos_client = careos_client

    def build_caregiver_dashboard(
        self,
        *,
        tenant_id: str,
        patient_id: str,
        actor_id: str,
        role: str,
    ) -> DashboardSummary:
        snapshot = self.careos_client.get_dashboard_snapshot(
            tenant_id=tenant_id,
            patient_id=patient_id,
            actor_id=actor_id,
            role=role,
        )
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
        return DashboardSummary.model_validate(snapshot)
