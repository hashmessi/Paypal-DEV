"""Data models and outcome enums for Deterministic Drift Engine."""

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class GateOutcome(str, Enum):
    MATCH = "MATCH"
    DRIFT = "DRIFT"
    HOLD = "HOLD"
    PROHIBITED = "PROHIBITED"


class Severity(str, Enum):
    BLOCKER = "BLOCKER"
    WARNING = "WARNING"
    INFO = "INFO"


class Finding(BaseModel):
    invariant_code: str
    severity: Severity
    message: str
    evidence_id: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None


class GateEvaluation(BaseModel):
    outcome: GateOutcome
    status_pill: str
    findings: List[Finding]
    can_capture: bool
    explanation: str
    evaluated_at: datetime

