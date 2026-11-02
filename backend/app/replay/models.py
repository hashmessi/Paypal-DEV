"""Pydantic schemas for Promise Replay timeline and audit (UI-03, LEDG-02)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReplayStep(BaseModel):
    step_number: int = Field(..., ge=1, le=10, description="Lifecycle sequence 1 through 10")
    name: str = Field(..., description="Display title for step")
    event_type: str = Field(..., description="Ledger event type or domain action")
    status: str = Field(..., description="COMPLETED | PENDING | DIVERGED | BLOCKED | FAILED")
    is_divergence: bool = Field(default=False, description="True if step marks where drift or gate block occurred")
    timestamp: Optional[str] = None
    actor: Optional[str] = None
    payload_summary: Optional[Dict[str, Any]] = None
    details: Optional[str] = None


class ReplayData(BaseModel):
    purchase_id: str
    steps: List[ReplayStep]
    current_step: int
    is_diverged: bool
    divergence_step: Optional[int] = None
    chain_intact: bool
    chain_event_count: int
    broken_step: Optional[int] = None
    gate_outcome: Optional[str] = None
    status_pill: Optional[str] = None

    counterfactual: Optional[Dict[str, Any]] = None
