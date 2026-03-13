from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models import CareEvent, Escalation, Medication, Patient, TaskCriticality

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
    TaskCriticality("Medication reminder", "non_negotiable", "Non-negotiable"),
    TaskCriticality("Symptom check", "flexible", "Flexible"),
    TaskCriticality("Walk reminder", "optional", "Optional"),
]

CAREGIVER_MAPPINGS = {
    "+14085157095": {
        "tenant_id": "tenant_001",
        "patient_id": "patient_123",
        "actor_id": "caregiver_999",
        "role": "caregiver",
        "phone_number": "+14085157095",
    }
}
