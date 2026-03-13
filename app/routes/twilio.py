from __future__ import annotations

from fastapi import APIRouter, Form, Response

from app.dependencies import authorization_service, openclaw_ingress_service
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

    context = authorization_service.resolve_caregiver_context(From)
    if context is None:
        reply = "We could not match this caregiver number to an active OpenClaw caregiver profile."
        return Response(content=twiml_message(reply), media_type="text/xml")

    link = openclaw_ingress_service.issue_dashboard_link_from_phone(phone_number=From)
    if link is None:
        reply = "This caregiver does not have an active dashboard authorization grant."
        return Response(content=twiml_message(reply), media_type="text/xml")
    reply = f"Open caregiver dashboard: {link['url']} (expires in 30 minutes)"
    return Response(content=twiml_message(reply), media_type="text/xml")
