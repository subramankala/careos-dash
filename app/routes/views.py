from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import careos_client, dashboard_service
from app.schemas import NotificationSettingsUpdateRequest
from app.security import ExpiredViewTokenError, InvalidViewTokenError, decode_view_token

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "base.html",
        {
            "page_title": "Ginger CareOS Dash",
            "content_only": True,
            "content_html": """
            <div class='max-w-xl mx-auto mt-12 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm'>
              <h1 class='text-3xl font-semibold text-slate-900'>Ginger CareOS Dash</h1>
              <p class='mt-4 text-slate-600'>Signed-link caregiver dashboard MVP.</p>
              <p class='mt-3 text-sm text-slate-500'>Use <code>POST /twilio/inbound</code> or <code>POST /generate-view</code> to create links.</p>
            </div>
            """,
        },
    )


def _decode_dashboard_claims(token: str):
    try:
        claims = decode_view_token(token)
    except ExpiredViewTokenError as exc:
        raise HTTPException(status_code=401, detail="expired dashboard token") from exc
    except InvalidViewTokenError as exc:
        raise HTTPException(status_code=401, detail="invalid dashboard token") from exc
    if claims.role != "caregiver" or claims.allowed_view != "caregiver_dashboard":
        raise HTTPException(status_code=403, detail="view not allowed")
    return claims


@router.get("/v/{token}", response_class=HTMLResponse)
def view_dashboard(request: Request, token: str) -> HTMLResponse:
    try:
        claims = _decode_dashboard_claims(token)
    except HTTPException as exc:
        if exc.status_code == 401 and exc.detail == "expired dashboard token":
            return templates.TemplateResponse(request, "error_expired_link.html", status_code=401)
        if exc.status_code == 401:
            return templates.TemplateResponse(request, "error_invalid_link.html", status_code=401)
        raise

    dashboard = dashboard_service.build_caregiver_dashboard(
        tenant_id=claims.tenant_id,
        patient_id=claims.patient_id,
        actor_id=claims.actor_id,
        role=claims.role,
    )
    return templates.TemplateResponse(
        request,
        "caregiver_dashboard.html",
        {
            "dashboard": dashboard,
            "token_claims": claims,
        },
    )


@router.get("/v/{token}/notification-settings")
def get_notification_settings(token: str) -> JSONResponse:
    claims = _decode_dashboard_claims(token)
    settings_payload = careos_client.get_notification_settings(
        actor_id=claims.actor_id,
        patient_id=claims.patient_id,
    )
    return JSONResponse(
        {
            "actor_id": settings_payload.actor_id,
            "patient_id": settings_payload.patient_id,
            "preset": settings_payload.preset,
            "channels": settings_payload.channels,
            "authorization_version": settings_payload.authorization_version,
        }
    )


@router.post("/v/{token}/notification-settings")
def update_notification_settings(token: str, payload: NotificationSettingsUpdateRequest) -> JSONResponse:
    claims = _decode_dashboard_claims(token)
    settings_payload = careos_client.update_notification_settings(
        actor_id=claims.actor_id,
        patient_id=claims.patient_id,
        channels=payload.channels,
    )
    return JSONResponse(
        {
            "actor_id": settings_payload.actor_id,
            "patient_id": settings_payload.patient_id,
            "preset": settings_payload.preset,
            "channels": settings_payload.channels,
            "authorization_version": settings_payload.authorization_version,
        }
    )
