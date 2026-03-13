from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.dependencies import url_service
from app.schemas import GenerateViewRequest, GenerateViewResponse

router = APIRouter()


@router.post("/generate-view", response_model=GenerateViewResponse)
def generate_view(payload: GenerateViewRequest) -> GenerateViewResponse:
    if payload.role != "caregiver" or payload.view != "caregiver_dashboard":
        raise HTTPException(status_code=403, detail="unsupported view request")
    result = url_service.generate_view_url(
        tenant_id=payload.tenant_id,
        patient_id=payload.patient_id,
        actor_id=payload.actor_id,
        role=payload.role,
        view=payload.view,
    )
    return GenerateViewResponse(**result)
