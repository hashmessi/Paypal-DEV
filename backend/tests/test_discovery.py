"""Tests for Channel3 Product Discovery and Merchant Quotes (DISC-01, DISC-02, DISC-03)."""

import pytest

from app.discovery.adapter import Channel3Adapter, normalize_condition
from app.discovery.models import CurrencyNotSupportedError


@pytest.mark.asyncio
async def test_channel3_search_candidates():
    """DISC-01: Search returns product candidates with offers and variants."""
    adapter = Channel3Adapter()
    results = await adapter.search("headphones")

    assert len(results) >= 1
    prod = results[0]
    assert "WH-1000XM5" in prod.title
    assert len(prod.offers) >= 3


def test_null_condition_is_unverified():
    """DISC-02: condition: null is treated as UNVERIFIED, never NEW."""
    assert normalize_condition(None) == "UNVERIFIED"
    assert normalize_condition("new") == "NEW"
    assert normalize_condition("brand new") == "NEW"
    assert normalize_condition("refurbished") == "REFURBISHED"
    assert normalize_condition("unknown") == "UNVERIFIED"

    adapter = Channel3Adapter()
    null_offer = adapter.get_offer_by_id("OFFER-BARGAIN-NULL-COND")
    assert null_offer is not None
    assert null_offer.condition == "UNVERIFIED"
    # Ensure raw payload is preserved
    assert null_offer.raw_payload["condition"] is None


def test_non_usd_offer_rejected():
    """DISC-02: Non-USD offers are rejected."""
    adapter = Channel3Adapter()
    euro_offer = adapter.get_offer_by_id("OFFER-EURO-EUR-NONUSD")
    assert euro_offer is not None
    assert euro_offer.currency == "EUR"

    with pytest.raises(CurrencyNotSupportedError) as exc_info:
        adapter.generate_merchant_quote("OFFER-EURO-EUR-NONUSD")
    assert "Only USD is accepted" in str(exc_info.value)


def test_merchant_quote_labeling():
    """DISC-03: Merchant quote confirmed separately and labeled 'Sandbox stand-in for <domain>'."""
    adapter = Channel3Adapter()
    quote = adapter.generate_merchant_quote("OFFER-APEX-NEW-BLK")

    assert quote.merchant_name == "Apex Electronics"
    assert quote.merchant_domain == "apextech.com"
    assert quote.label == "Sandbox stand-in for apextech.com"
    assert quote.subtotal_cents == 8999
    assert quote.total_cents == 8999
    assert quote.currency == "USD"
    assert quote.condition == "NEW"
    assert quote.color == "black"

