from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models import AuthorizationGrant, CareEvent, Escalation, Medication, Patient, TaskCriticality

NOW = datetime(2026, 3, 13, 9, 30, tzinfo=UTC)

PATIENTS = {
    "patient_123": Patient(
        id="patient_123",
        tenant_id="tenant_001",
        full_name="Nageswara Rao",
        age=72,
        sex="Male",
        primary_conditions=["Coronary artery disease", "Type 2 diabetes", "Hypertension"],
        care_plan_name="Post-discharge cardiac recovery",
        last_check_in_at=NOW - timedelta(hours=2),
        timezone="Asia/Kolkata",
        primary_language="en",
        persona_type="caregiver_managed_elder",
        risk_level="medium",
        status="active",
    )
}

MEDICATIONS = {
    "patient_123": [
        Medication("med_1", "patient_123", "Brilinta", "90 mg", "08:00", "missed"),
        Medication("med_2", "patient_123", "Ecosprin", "75 mg", "14:00", "pending"),
        Medication("med_3", "patient_123", "Nikoran", "5 mg", "20:00", "pending"),
        Medication("med_4", "patient_123", "Gener Sita IR", "2/50/500 mg", "21:00", "pending"),
    ]
}

ESCALATIONS = {
    "patient_123": [
        Escalation(
            id="esc_1",
            patient_id="patient_123",
            type="missed_medication",
            severity="high",
            status="open",
            created_at=NOW - timedelta(hours=1, minutes=15),
            summary="Morning Brilinta dose missed and still unconfirmed.",
        ),
        Escalation(
            id="esc_2",
            patient_id="patient_123",
            type="symptom_concern",
            severity="medium",
            status="monitoring",
            created_at=NOW - timedelta(hours=4),
            summary="Patient reported mild dizziness during morning walk.",
        ),
    ]
}

CARE_EVENTS = {
    "patient_123": [
        CareEvent("evt_1", "patient_123", "medication_missed", "Brilinta morning dose missed", NOW - timedelta(hours=1, minutes=10), "open"),
        CareEvent("evt_2", "patient_123", "reminder_triggered", "Medication reminder sent", NOW - timedelta(hours=1, minutes=20), "sent"),
        CareEvent("evt_3", "patient_123", "symptom_check", "Dizziness symptom check submitted", NOW - timedelta(hours=4), "received"),
        CareEvent("evt_4", "patient_123", "walk_skipped", "Morning walk skipped", NOW - timedelta(hours=5, minutes=30), "logged"),
        CareEvent("evt_5", "patient_123", "medication_taken", "Pantop 40mg taken", NOW - timedelta(hours=6), "completed"),
        CareEvent("evt_6", "patient_123", "check_in", "Daily caregiver check-in completed", NOW - timedelta(hours=7), "completed"),
    ]
}

TASK_CRITICALITY = [
    TaskCriticality("Medication reminder", "NON_NEGOTIABLE", "Non-negotiable"),
    TaskCriticality("Symptom check", "FLEXIBLE_CLINICAL", "Flexible clinical"),
    TaskCriticality("Walk reminder", "OPTIONAL_LIFESTYLE", "Optional lifestyle"),
]

CAREGIVER_MAPPINGS = {
    "+14085157095": {
        "tenant_id": "tenant_001",
        "patient_id": "patient_123",
        "actor_id": "caregiver_999",
        "role": "caregiver",
        "phone_number": "+14085157095",
    },
    "+14085157096": {
        "tenant_id": "tenant_001",
        "patient_id": "patient_123",
        "actor_id": "caregiver_556",
        "role": "caregiver",
        "phone_number": "+14085157096",
    }
}

AUTHORIZATION_GRANTS = [
    AuthorizationGrant(
        authorization_id="auth_001",
        tenant_id="tenant_001",
        patient_id="patient_123",
        actor_id="caregiver_999",
        actor_type="caregiver",
        granted_by="patient_123",
        scopes=[
            "view_dashboard",
            "view_escalations",
            "view_medications",
            "view_recent_events",
            "view_criticality",
        ],
        status="active",
        effective_at=NOW - timedelta(days=10),
        revoked_at=None,
        authorization_version=3,
    ),
    AuthorizationGrant(
        authorization_id="auth_002",
        tenant_id="tenant_001",
        patient_id="patient_123",
        actor_id="caregiver_556",
        actor_type="caregiver",
        granted_by="patient_123",
        scopes=[
            "view_dashboard",
            "view_criticality",
        ],
        status="active",
        effective_at=NOW - timedelta(days=4),
        revoked_at=None,
        authorization_version=1,
    )
]
