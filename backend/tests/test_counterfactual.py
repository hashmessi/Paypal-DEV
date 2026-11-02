from decimal import Decimal

import pytest

from app.proof.counterfactual import counterfactual
from app.proof.runner import run_proof


def test_drift_blocked_avoids_full_amount():
    assert counterfactual(39900, True, 0) == {"naive_capture_cents": 39900, "gated_capture_cents": 0, "loss_avoided_cents": 39900}


def test_match_captured_avoids_nothing():
    r = counterfactual(39900, True, 39900)
    assert r["naive_capture_cents"] == r["gated_capture_cents"] and r["loss_avoided_cents"] == 0


def test_no_evidence_naive_captures_nothing():
    assert counterfactual(39900, False, 0)["loss_avoided_cents"] == 0


@pytest.mark.parametrize("bad", [399.0, Decimal("399.00")])
def test_non_int_raises(bad):
    with pytest.raises(TypeError):
        counterfactual(bad, True, 0)
    with pytest.raises(TypeError):
        counterfactual(39900, True, bad)


def test_proof_protected_total_is_integer_and_simulated():
    r = run_proof()
    p = r["protected"]
    assert isinstance(p["loss_avoided_cents"], int) and p["loss_avoided_cents"] > 0
    assert p["simulated"] is True
    assert p["loss_avoided_cents"] == sum(s["counterfactual"]["loss_avoided_cents"] for s in r["scenarios"])
