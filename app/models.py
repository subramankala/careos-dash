from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Patient:
    id: str
    tenant_id: str
    full_name: str
    age: int
    sex: str
    primary_conditions: list[str]
    care_plan_name: str
    last_check_in_at: datetime


@dataclass(frozen=True)
class Medication:
    id: str
    patient_id: str
    name: str
    dosage: str
    schedule_time: str
    status: str


@dataclass(frozen=True)
class Escalation:
    id: str
    patient_id: str
    type: str
    severity: str
    status: str
    created_at: datetime
    summary: str


@dataclass(frozen=True)
class CareEvent:
    id: str
    patient_id: str
    event_type: str
    title: str
    timestamp: datetime
    status: str


@dataclass(frozen=True)
class TaskCriticality:
    task_type: str
    criticality_level: str
    caregiver_visible_label: str
