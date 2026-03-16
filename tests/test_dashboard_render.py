from __future__ import annotations

from app.routes.views import view_dashboard
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
    )
    response = view_dashboard(_request(f"/v/{token}"), token)
    assert response.status_code == 200
    assert b"Nageswara Rao" in response.body
    assert b"Medication Adherence Snapshot" in response.body
    assert b"Notification Channels" in response.body
    assert b"Critical Alerts" in response.body
