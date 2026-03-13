from __future__ import annotations

from app.config import settings
from app.security import create_view_token


class SignedURLService:
    def generate_view_url(
        self,
        *,
        tenant_id: str,
        patient_id: str,
        actor_id: str,
        role: str,
        view: str,
    ) -> dict:
        token = create_view_token(
            tenant_id=tenant_id,
            patient_id=patient_id,
            actor_id=actor_id,
            role=role,
            allowed_view=view,
        )
        return {
            "url": f"{settings.base_url}/v/{token}",
            "expires_in_seconds": settings.link_expiry_seconds,
        }
