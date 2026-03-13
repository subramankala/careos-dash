from __future__ import annotations

from app.schemas import AuthorizationContext, CaregiverContext, ViewAccess
from app.services.careos_client import CareOSMCPClient


class AuthorizationService:
    def __init__(self, careos_client: CareOSMCPClient) -> None:
        self.careos_client = careos_client

    def resolve_caregiver_context(self, phone_number: str) -> CaregiverContext | None:
        return self.careos_client.resolve_caregiver_context(phone_number)

    def require_view_access(
        self,
        *,
        actor_id: str,
        patient_id: str,
        tenant_id: str,
        role: str,
        view: str,
    ) -> ViewAccess | None:
        if role != "caregiver" or view != "caregiver_dashboard":
            return None
        grant = self.careos_client.get_active_authorization_grant(
            actor_id=actor_id,
            patient_id=patient_id,
            tenant_id=tenant_id,
        )
        if grant is None or "view_dashboard" not in grant.scopes:
            return None
        return ViewAccess(
            tenant_id=tenant_id,
            patient_id=patient_id,
            actor_id=actor_id,
            role=role,
            view=view,
            authorization_version=grant.authorization_version,
            scopes=sorted(grant.scopes),
        )

    def revalidate_view_access(
        self,
        *,
        actor_id: str,
        patient_id: str,
        tenant_id: str,
        role: str,
        view: str,
        authorization_version: int,
    ) -> AuthorizationContext | None:
        access = self.require_view_access(
            actor_id=actor_id,
            patient_id=patient_id,
            tenant_id=tenant_id,
            role=role,
            view=view,
        )
        if access is None or access.authorization_version != authorization_version:
            return None
        return AuthorizationContext(
            actor_id=actor_id,
            patient_id=patient_id,
            tenant_id=tenant_id,
            role=role,
            scopes=access.scopes,
            authorization_version=access.authorization_version,
        )
