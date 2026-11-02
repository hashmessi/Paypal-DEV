"""Tests for Intent Extraction, Clock-relative Deadlines, and Caching (INTENT-01, INTENT-02, INTENT-03)."""

from datetime import date, timedelta
import pytest
from sqlalchemy.orm import Session

from app.core.clock import FixedClock
from app.core.models import ExtractionCache
from app.intent.extractor import IntentExtractor
from app.intent.fallback import extract_fallback_constraints


def test_deterministic_fallback_extractor():
    """Verify rule-based fallback extracts all key constraints accurately without network."""
    instruction = "new black over-ear headphones under $100, arrive within 5 days"
    constraints = extract_fallback_constraints(instruction)

    assert "headphone" in constraints.product_type
    assert constraints.condition == "new"
    assert constraints.color == "black"
    assert constraints.max_total_cents == 10000
    assert constraints.currency == "USD"
    assert constraints.deliver_within_days == 5
    assert constraints.substitutions_allowed is False


def test_fallback_extractor_refurbished_and_price_variations():
    """Verify variations of refurbished, custom price, and alternative delivery windows."""
    inst1 = "Sony wireless headphones refurbished under $89.50 in 3 days"
    c1 = extract_fallback_constraints(inst1)
    assert c1.condition == "refurbished"
    assert c1.max_total_cents == 8950
    assert c1.deliver_within_days == 3

    inst2 = "silver noise canceling headphones max $150 substitutions allowed"
    c2 = extract_fallback_constraints(inst2)
    assert c2.color == "silver"
    assert c2.max_total_cents == 15000
    assert c2.substitutions_allowed is True


@pytest.mark.asyncio
async def test_extractor_clock_relative_deadline(db_session: Session, fixed_clock: FixedClock):
    """INTENT-02: Delivery deadlines are relative and resolved against injected Clock in code."""
    extractor = IntentExtractor(db=db_session, clock=fixed_clock)
    instruction = "new black over-ear headphones under $100, arrive within 4 days"

    result = await extractor.extract(instruction)

    assert result.constraints.deliver_within_days == 4
    # fixed_clock date is 2026-11-01
    expected_deadline = fixed_clock.today() + timedelta(days=4)
    assert result.resolved_deadline == expected_deadline
    assert result.resolved_deadline == date(2026, 11, 5)


@pytest.mark.asyncio
async def test_extractor_source_tagging_and_cache(db_session: Session, fixed_clock: FixedClock):
    """INTENT-03: Result tagged with source ('ai' or 'fallback'), second call hits extraction_cache."""
    extractor = IntentExtractor(db=db_session, clock=fixed_clock)
    instruction = "new black over-ear headphones under $99"

    # First call (fallback because no Gemini/OpenRouter keys in test)
    res1 = await extractor.extract(instruction)
    assert res1.source == "fallback"

    # Verify cache record exists in DB
    cached_row = db_session.query(ExtractionCache).filter_by(instruction_hash=res1.instruction_hash).first()
    assert cached_row is not None
    assert cached_row.source == "fallback"

    # Second call must hit cache
    res2 = await extractor.extract(instruction)
    assert res2.instruction_hash == res1.instruction_hash
    assert res2.constraints.max_total_cents == res1.constraints.max_total_cents

