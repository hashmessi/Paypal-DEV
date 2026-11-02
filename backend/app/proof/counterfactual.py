"""Naive-vs-gated counterfactual: what an ungated agent+PayPal flow would have captured. Pure, integer cents."""

from typing import Dict

from app.core.config import settings


def gateway_is_simulated() -> bool:
    """True when FakeGateway serves requests (single source of truth, also used by api.deps.get_gateway)."""
    return settings.PAYPAL_CLIENT_ID in ("test", "sandbox_test") or bool(settings.DEMO_MODE)


def counterfactual(authorized_cents: int, has_evidence: bool, captured_cents: int) -> Dict[str, int]:
    for v in (authorized_cents, captured_cents):
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError("money must be integer cents")
    # A naive flow captures on any merchant claim with no drift check; no claim -> nothing to act on.
    naive = authorized_cents if has_evidence else 0
    return {
        "naive_capture_cents": naive,
        "gated_capture_cents": captured_cents,
        "loss_avoided_cents": max(0, naive - captured_cents),
    }
