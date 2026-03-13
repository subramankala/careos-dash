from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_mcp_tools_reject_invalid_api_key() -> None:
    previous_key = settings.mcp_api_key
    settings.mcp_api_key = "test-key"
    try:
        response = client.get("/mcp/tools", headers={"x-mcp-api-key": "wrong"})
        assert response.status_code == 401
    finally:
        settings.mcp_api_key = previous_key


def test_mcp_tools_list_available_tool() -> None:
    previous_key = settings.mcp_api_key
    settings.mcp_api_key = "test-key"
    try:
        response = client.get("/mcp/tools", headers={"x-mcp-api-key": "test-key"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["tools"][0]["name"] == "dash_generate_caregiver_dashboard"
    finally:
        settings.mcp_api_key = previous_key


def test_mcp_call_generates_caregiver_dashboard_url_from_phone_number() -> None:
    previous_key = settings.mcp_api_key
    settings.mcp_api_key = "test-key"
    try:
        response = client.post(
            "/mcp/call",
            headers={"x-mcp-api-key": "test-key"},
            json={
                "tool": "dash_generate_caregiver_dashboard",
                "arguments": {"phone_number": "+14085157095"},
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert "/v/" in payload["result"]["url"]
        assert payload["result"]["expires_in_seconds"] == 1800
    finally:
        settings.mcp_api_key = previous_key
