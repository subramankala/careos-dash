from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.dependencies import authorization_service, dashboard_service
from app.logging import get_logger, log_event
from app.security import ExpiredViewTokenError, InvalidViewTokenError, decode_view_token

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = get_logger("dashboard_views")


@router.get("/", response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "base.html",
        {
            "page_title": "Ginger Care-Dash",
            "content_only": True,
            "content_html": f"""
            <div class='max-w-xl mx-auto mt-12 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm'>
              <h1 class='text-3xl font-semibold text-slate-900'>Ginger Care-Dash</h1>
              <p class='mt-4 text-slate-600'>Secure caregiver dashboard rendered behind {settings.openclaw_name}.</p>
              <p class='mt-3 text-sm text-slate-500'>Use <code>POST /twilio/inbound</code> or <code>POST /generate-view</code> to issue links.</p>
            </div>
            """,
        },
    )


@router.get("/v/{token}", response_class=HTMLResponse)
def view_dashboard(request: Request, token: str) -> HTMLResponse:
    try:
        claims = decode_view_token(token)
    except ExpiredViewTokenError:
        log_event(logger, "dashboard_access_denied", reason="expired_token")
        return templates.TemplateResponse(request, "error_expired_link.html", status_code=401)
    except InvalidViewTokenError:
        log_event(logger, "dashboard_access_denied", reason="invalid_token")
        return templates.TemplateResponse(request, "error_invalid_link.html", status_code=401)

    if claims.role != "caregiver" or claims.allowed_view != "caregiver_dashboard":
        log_event(
            logger,
            "dashboard_access_denied",
            reason="role_or_view_mismatch",
            actor_id=claims.actor_id,
            patient_id=claims.patient_id,
        )
        raise HTTPException(status_code=403, detail="view not allowed")

    auth_context = authorization_service.revalidate_view_access(
        actor_id=claims.actor_id,
        patient_id=claims.patient_id,
        tenant_id=claims.tenant_id,
        role=claims.role,
        view=claims.allowed_view,
        authorization_version=claims.authorization_version,
    )
    if auth_context is None:
        log_event(
            logger,
            "dashboard_access_denied",
            reason="authorization_revalidation_failed",
            actor_id=claims.actor_id,
            patient_id=claims.patient_id,
            tenant_id=claims.tenant_id,
            authorization_version=claims.authorization_version,
        )
        return templates.TemplateResponse(request, "error_unauthorized.html", status_code=403)

    dashboard = dashboard_service.build_caregiver_dashboard(
        auth_context=auth_context,
    )
    log_event(
        logger,
        "dashboard_access_granted",
        actor_id=claims.actor_id,
        patient_id=claims.patient_id,
        tenant_id=claims.tenant_id,
        authorization_version=claims.authorization_version,
        section_visibility=dashboard.section_visibility,
    )
    return templates.TemplateResponse(
        request,
        "caregiver_dashboard.html",
        {
            "dashboard": dashboard,
            "token_claims": claims,
            "auth_context": auth_context,
        },
    )
