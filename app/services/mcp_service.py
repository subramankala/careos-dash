from __future__ import annotations

from fastapi import HTTPException

from app.services.careos_client import MockCareOSClient
from app.services.url_service import SignedURLService


class MCPService:
    def __init__(self, careos_client: MockCareOSClient, url_service: SignedURLService) -> None:
        self._careos_client = careos_client
        self._url_service = url_service

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": "dash_generate_caregiver_dashboard",
                "description": "Generate a signed caregiver dashboard link for a caregiver and patient context.",
                "write": False,
            }
        ]

    def call_tool(self, tool: str, arguments: dict) -> dict:
        if tool != "dash_generate_caregiver_dashboard":
            raise HTTPException(status_code=404, detail="unknown tool")
        return self._generate_caregiver_dashboard(arguments)

    def _generate_caregiver_dashboard(self, arguments: dict) -> dict:
        phone_number = str(arguments.get("phone_number", "")).strip()
        if phone_number:
            context = self._careos_client.resolve_caregiver_context(phone_number)
            if context is None:
                raise HTTPException(status_code=404, detail="unknown caregiver phone number")
            tenant_id = context.tenant_id
            patient_id = context.patient_id
            actor_id = context.actor_id
            role = context.role
        else:
            tenant_id = str(arguments.get("tenant_id", "")).strip()
            patient_id = str(arguments.get("patient_id", "")).strip()
            actor_id = str(arguments.get("actor_id", "")).strip()
            role = str(arguments.get("role", "caregiver")).strip() or "caregiver"
            if not tenant_id or not patient_id or not actor_id:
                raise HTTPException(
                    status_code=400,
                    detail="tenant_id, patient_id, and actor_id are required when phone_number is not provided",
                )
        if role != "caregiver":
            raise HTTPException(status_code=403, detail="only caregiver dashboard links are supported")
        return self._url_service.generate_view_url(
            tenant_id=tenant_id,
            patient_id=patient_id,
            actor_id=actor_id,
            role=role,
            view="caregiver_dashboard",
        )
