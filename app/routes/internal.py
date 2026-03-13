from __future__ import annotations

from fastapi import APIRouter

from app.dependencies import openclaw_ingress_service
from app.schemas import GenerateViewRequest, GenerateViewResponse

router = APIRouter()


@router.post("/generate-view", response_model=GenerateViewResponse)
def generate_view(payload: GenerateViewRequest) -> GenerateViewResponse:
    result = openclaw_ingress_service.generate_authorized_view(payload)
    return GenerateViewResponse(**result)
