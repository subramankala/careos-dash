from __future__ import annotations

from fastapi import FastAPI

from app.routes.internal import router as internal_router
from app.routes.twilio import router as twilio_router
from app.routes.views import router as view_router

app = FastAPI(title="Ginger CareOS Dash")
app.include_router(twilio_router)
app.include_router(internal_router)
app.include_router(view_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"service": "ginger-careos-dash", "status": "ok"}
