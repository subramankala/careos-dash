from __future__ import annotations


SUPPORTED_DASHBOARD_PHRASES = {
    "show caregiver dashboard",
    "show dashboard",
    "caregiver dashboard",
    "show progress",
    "show patient status",
}


def parse_inbound_intent(text: str) -> str | None:
    normalized = " ".join(text.strip().lower().split())
    if normalized in SUPPORTED_DASHBOARD_PHRASES:
        return "caregiver_dashboard"
    return None
