from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SignedViewClaims(BaseModel):
    tenant_id: str
    patient_id: str
    actor_id: str
    role: Literal["caregiver", "patient", "clinician"]
    allowed_view: Literal["caregiver_dashboard"]
    iat: int
    exp: int
    jti: str


class GenerateViewRequest(BaseModel):
    tenant_id: str
    patient_id: str
    actor_id: str
    role: Literal["caregiver", "patient", "clinician"]
    view: Literal["caregiver_dashboard"]


class GenerateViewResponse(BaseModel):
    url: str
    expires_in_seconds: int


class CaregiverContext(BaseModel):
    tenant_id: str
    patient_id: str
    actor_id: str
    role: Literal["caregiver"]
    phone_number: str


class DashboardSummary(BaseModel):
    patient: dict
    medications: list[dict]
    escalations: list[dict]
    recent_events: list[dict]
    criticality_legend: list[dict]
    adherence: dict


class TwilioInboundPayload(BaseModel):
    From: str = Field(default="")
    To: str = Field(default="")
    Body: str = Field(default="")
    MessageSid: str = Field(default="")
