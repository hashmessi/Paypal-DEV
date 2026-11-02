"""Intent extraction API endpoint."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_clock
from app.api.guards import rate_limit_llm
from app.core.clock import Clock
from app.core.db import get_db
from app.intent.extractor import IntentExtractor
from app.intent.models import ExtractedIntent

router = APIRouter(prefix="/intent", tags=["intent"])


class ExtractIntentRequest(BaseModel):
    instruction: str = Field(
        ...,
        description="Buyer natural language purchase prompt",
        json_schema_extra={"example": "new black over-ear headphones under $100, arrive within 5 days"},
    )


@router.post("/extract", response_model=ExtractedIntent, dependencies=[Depends(rate_limit_llm)])
async def extract_intent(
    req: ExtractIntentRequest,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
):
    """Extract strict typed constraints from natural language prompt.

    INTENT-01: Multi-tier extraction (Gemini -> OpenRouter -> Deterministic Fallback).
    INTENT-02: Delivery deadlines resolved in code against Clock (no calendar dates).
    INTENT-03: Returns extraction source ('ai' or 'fallback') for UI badge.
    """
    extractor = IntentExtractor(db=db, clock=clock)
    result = await extractor.extract(instruction=req.instruction)
    return result

