from __future__ import annotations

from fastapi import APIRouter, Form, Response

from app.dependencies import careos_client, url_service
from app.intent import parse_inbound_intent
from app.services.twilio_service import twiml_message

router = APIRouter()


@router.post("/twilio/inbound")
def twilio_inbound(
    From: str = Form(default=""),
    To: str = Form(default=""),
    Body: str = Form(default=""),
    MessageSid: str = Form(default=""),
) -> Response:
    intent = parse_inbound_intent(Body)
    if intent is None:
        reply = "Supported commands: show caregiver dashboard, show dashboard, show progress, show patient status."
        return Response(content=twiml_message(reply), media_type="text/xml")

    context = careos_client.resolve_caregiver_context(From)
    if context is None:
        reply = "We could not match this caregiver number to a dashboard profile."
        return Response(content=twiml_message(reply), media_type="text/xml")

    link = url_service.generate_view_url(
        tenant_id=context.tenant_id,
        patient_id=context.patient_id,
        actor_id=context.actor_id,
        role=context.role,
        view="caregiver_dashboard",
    )
    reply = f"Open caregiver dashboard: {link['url']} (expires in 30 minutes)"
    return Response(content=twiml_message(reply), media_type="text/xml")
