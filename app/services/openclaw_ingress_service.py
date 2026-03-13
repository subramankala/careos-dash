from __future__ import annotations

from fastapi import HTTPException

from app.logging import get_logger, log_event
from app.schemas import GenerateViewRequest
from app.services.authorization_service import AuthorizationService
from app.services.url_service import SignedURLService


class OpenClawIngressService:
    """OpenClaw-facing orchestration for caregiver dashboard link issuance."""

    def __init__(self, authorization_service: AuthorizationService, url_service: SignedURLService) -> None:
        self.authorization_service = authorization_service
        self.url_service = url_service
        self.logger = get_logger("openclaw_ingress")

    def generate_authorized_view(self, payload: GenerateViewRequest) -> dict:
        if payload.role != "caregiver" or payload.view != "caregiver_dashboard":
            log_event(
                self.logger,
                "view_link_rejected",
                reason="unsupported_view_request",
                actor_id=payload.actor_id,
                patient_id=payload.patient_id,
                tenant_id=payload.tenant_id,
                view=payload.view,
            )
            raise HTTPException(status_code=403, detail="unsupported view request")
        access = self.authorization_service.require_view_access(
            actor_id=payload.actor_id,
            patient_id=payload.patient_id,
            tenant_id=payload.tenant_id,
            role=payload.role,
            view=payload.view,
        )
        if access is None:
            log_event(
                self.logger,
                "view_link_rejected",
                reason="missing_active_grant",
                actor_id=payload.actor_id,
                patient_id=payload.patient_id,
                tenant_id=payload.tenant_id,
                view=payload.view,
            )
            raise HTTPException(status_code=403, detail="active authorization grant required")
        result = self.url_service.generate_view_url(
            tenant_id=payload.tenant_id,
            patient_id=payload.patient_id,
            actor_id=payload.actor_id,
            role=payload.role,
            view=payload.view,
            authorization_version=access.authorization_version,
        )
        log_event(
            self.logger,
            "view_link_issued",
            actor_id=payload.actor_id,
            patient_id=payload.patient_id,
            tenant_id=payload.tenant_id,
            view=payload.view,
            authorization_version=access.authorization_version,
            scopes=access.scopes,
        )
        return result

    def issue_dashboard_link_from_phone(self, *, phone_number: str) -> dict | None:
        context = self.authorization_service.resolve_caregiver_context(phone_number)
        if context is None:
            log_event(self.logger, "phone_resolution_failed", phone_number=phone_number)
            return None
        access = self.authorization_service.require_view_access(
            actor_id=context.actor_id,
            patient_id=context.patient_id,
            tenant_id=context.tenant_id,
            role=context.role,
            view="caregiver_dashboard",
        )
        if access is None:
            log_event(
                self.logger,
                "view_link_rejected",
                reason="missing_active_grant",
                actor_id=context.actor_id,
                patient_id=context.patient_id,
                tenant_id=context.tenant_id,
                view="caregiver_dashboard",
            )
            return None
        result = self.url_service.generate_view_url(
            tenant_id=context.tenant_id,
            patient_id=context.patient_id,
            actor_id=context.actor_id,
            role=context.role,
            view="caregiver_dashboard",
            authorization_version=access.authorization_version,
        )
        log_event(
            self.logger,
            "view_link_issued",
            actor_id=context.actor_id,
            patient_id=context.patient_id,
            tenant_id=context.tenant_id,
            view="caregiver_dashboard",
            authorization_version=access.authorization_version,
            scopes=access.scopes,
            phone_number=phone_number,
        )
        return result
