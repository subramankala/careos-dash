from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.config import settings
from app.schemas import SignedViewClaims


class InvalidViewTokenError(Exception):
    """Raised when a dashboard link token is invalid."""


class ExpiredViewTokenError(Exception):
    """Raised when a dashboard link token has expired."""


def create_view_token(
    *,
    tenant_id: str,
    patient_id: str,
    actor_id: str,
    role: str,
    allowed_view: str,
    authorization_version: int,
    expires_in_seconds: int | None = None,
) -> str:
    now = datetime.now(UTC)
    expiry_seconds = expires_in_seconds or settings.link_expiry_seconds
    payload = SignedViewClaims(
        tenant_id=tenant_id,
        patient_id=patient_id,
        actor_id=actor_id,
        role=role,
        allowed_view=allowed_view,
        authorization_version=authorization_version,
        iat=int(now.timestamp()),
        exp=int((now + timedelta(seconds=expiry_seconds)).timestamp()),
        jti=str(uuid4()),
    )
    return jwt.encode(payload.model_dump(), settings.signing_secret, algorithm="HS256")


def decode_view_token(token: str) -> SignedViewClaims:
    try:
        payload = jwt.decode(token, settings.signing_secret, algorithms=["HS256"])
    except ExpiredSignatureError as exc:
        raise ExpiredViewTokenError from exc
    except InvalidTokenError as exc:
        raise InvalidViewTokenError from exc
    return SignedViewClaims.model_validate(payload)
