from __future__ import annotations

from app.intent import parse_inbound_intent


def test_supported_dashboard_intents_map_correctly() -> None:
    assert parse_inbound_intent("show caregiver dashboard") == "caregiver_dashboard"
    assert parse_inbound_intent("show dashboard") == "caregiver_dashboard"
    assert parse_inbound_intent("show progress") == "caregiver_dashboard"


def test_unknown_intent_returns_none() -> None:
    assert parse_inbound_intent("hello there") is None
