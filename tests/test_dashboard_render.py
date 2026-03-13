from __future__ import annotations

from app.dependencies import dashboard_service
from app.routes.views import view_dashboard
from app.schemas import AuthorizationContext
from app.security import create_view_token
from starlette.requests import Request


def _request(path: str) -> Request:
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


def test_dashboard_renders_for_valid_token() -> None:
    token = create_view_token(
        tenant_id="tenant_001",
        patient_id="patient_123",
        actor_id="caregiver_999",
        role="caregiver",
        allowed_view="caregiver_dashboard",
        authorization_version=3,
    )
    response = view_dashboard(_request(f"/v/{token}"), token)
    assert response.status_code == 200
    assert b"Nageswara Rao" in response.body
    assert b"Medication Adherence Snapshot" in response.body
    assert b"Risk Medium" in response.body
    assert b"Persona" in response.body


def test_dashboard_hides_sections_for_downgraded_grant() -> None:
    dashboard = dashboard_service.build_caregiver_dashboard(
        auth_context=AuthorizationContext(
            actor_id="caregiver_556",
            patient_id="patient_123",
            tenant_id="tenant_001",
            role="caregiver",
            scopes=["view_criticality", "view_dashboard"],
            authorization_version=1,
        )
    )
    assert dashboard.section_visibility["medications"] is False
    assert dashboard.section_visibility["escalations"] is False
    assert dashboard.section_visibility["recent_events"] is False
    assert dashboard.section_visibility["criticality_legend"] is True
    assert dashboard.medications == []
    assert dashboard.criticality_legend
