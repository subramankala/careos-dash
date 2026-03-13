from __future__ import annotations

import pytest

from app.dependencies import authorization_service
from app.routes.internal import generate_view
from app.routes.views import view_dashboard
from app.schemas import GenerateViewRequest
from app.security import create_view_token
from starlette.requests import Request


def _request(path: str = "/") -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "raw_path": path.encode(),
        "scheme": "http",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 123),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_active_grant_required_for_generate_view() -> None:
    with pytest.raises(Exception) as exc_info:
        generate_view(
            GenerateViewRequest(
                tenant_id="tenant_001",
                patient_id="patient_123",
                actor_id="caregiver_missing",
                role="caregiver",
                view="caregiver_dashboard",
            )
        )
    assert getattr(exc_info.value, "status_code", None) == 403


def test_version_mismatched_link_is_rejected() -> None:
    token = create_view_token(
        tenant_id="tenant_001",
        patient_id="patient_123",
        actor_id="caregiver_999",
        role="caregiver",
        allowed_view="caregiver_dashboard",
        authorization_version=2,
    )
    response = view_dashboard(_request(f"/v/{token}"), token)
    assert response.status_code == 403
    assert b"no longer authorized" in response.body


def test_authorization_service_revalidates_current_version() -> None:
    auth_context = authorization_service.revalidate_view_access(
        actor_id="caregiver_999",
        patient_id="patient_123",
        tenant_id="tenant_001",
        role="caregiver",
        view="caregiver_dashboard",
        authorization_version=3,
    )
    assert auth_context is not None
    assert "view_dashboard" in auth_context.scopes


def test_downgraded_grant_revalidates_with_limited_scopes() -> None:
    auth_context = authorization_service.revalidate_view_access(
        actor_id="caregiver_556",
        patient_id="patient_123",
        tenant_id="tenant_001",
        role="caregiver",
        view="caregiver_dashboard",
        authorization_version=1,
    )
    assert auth_context is not None
    assert auth_context.scopes == ["view_criticality", "view_dashboard"]
