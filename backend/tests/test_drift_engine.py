"""Unit tests for Pure Deterministic Invariant Drift Engine (INV-01 to INV-06, DRIFT-01, DRIFT-03, PAY-07)."""

from datetime import datetime, timedelta, timezone
import json
import pytest

from app.core.models import FulfillmentEvidence, PaymentAuthorization, PromiseReceipt
from app.drift.engine import evaluate
from app.drift.explainer import generate_explanation
from app.drift.invariants import check_auth_expiry, check_fulfillment_invariants
from app.drift.models import Finding, GateOutcome, Severity


def create_mock_receipt(
    expected_sku: str = "WH1000XM5-BLK-NEW",
    expected_color: str = "black",
    reject_refurbished: bool = True,
    max_delivery_days: int = 5,
    created_at: datetime = datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc),
) -> PromiseReceipt:
    conditions = {
        "expected_sku": expected_sku,
        "expected_color": expected_color,
        "reject_refurbished": reject_refurbished,
        "max_delivery_days": max_delivery_days,
    }
    return PromiseReceipt(
        purchase_id="test-purchase-01",
        version=1,
        receipt_hash="0" * 64,
        capture_conditions_json=json.dumps(conditions),
        total_cents=39900,
        currency="USD",
        created_at=created_at,
    )


def create_mock_auth(
    expiration_time: datetime,
    state: str = "authorized",
) -> PaymentAuthorization:
    return PaymentAuthorization(
        purchase_id="test-purchase-01",
        authorization_id="AUTH-12345",
        order_id="ORDER-12345",
        state=state,
        amount_cents=39900,
        currency="USD",
        expiration_time=expiration_time,
        created_at=datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc),
    )


def test_inv_01_condition_refurbished_causes_drift():
    receipt = create_mock_receipt()
    evidence = [
        FulfillmentEvidence(
            purchase_id="test-purchase-01",
            seq=1,
            source="carrier",
            external_event_id="EVT-01",
            trust_level="CARRIER_TELEMETRY",
            carrier_status="ACCEPTED",
            sku="WH1000XM5-BLK-NEW",
            condition="REFURBISHED",
            color="black",
        )
    ]
    findings = check_fulfillment_invariants(receipt, evidence, now=datetime(2026, 12, 2, 12, 0, tzinfo=timezone.utc))
    assert any(f.invariant_code == "INV-01-CONDITION" and f.severity == Severity.BLOCKER for f in findings)

    eval_res = evaluate(receipt, None, evidence, now=datetime(2026, 12, 2, 12, 0, tzinfo=timezone.utc))
    assert eval_res.outcome == GateOutcome.DRIFT
    assert eval_res.status_pill == "CAPTURE BLOCKED"
    assert eval_res.can_capture is False


def test_inv_02_sku_and_color_mismatch_causes_drift():
    receipt = create_mock_receipt(expected_sku="WH1000XM5-BLK-NEW", expected_color="black")
    # SKU mismatch
    ev_sku_drift = [
        FulfillmentEvidence(
            purchase_id="test-purchase-01",
            seq=1,
            source="carrier",
            external_event_id="EVT-01",
            trust_level="CARRIER_TELEMETRY",
            carrier_status="ACCEPTED",
            sku="WH1000XM4-OLD",
            condition="NEW",
            color="black",
        )
    ]
    eval_sku = evaluate(receipt, None, ev_sku_drift, now=datetime(2026, 12, 2, 12, 0, tzinfo=timezone.utc))
    assert eval_sku.outcome == GateOutcome.DRIFT
    assert any(f.invariant_code == "INV-02-SKU" for f in eval_sku.findings)

    # Color mismatch
    ev_color_drift = [
        FulfillmentEvidence(
            purchase_id="test-purchase-01",
            seq=1,
            source="carrier",
            external_event_id="EVT-02",
            trust_level="CARRIER_TELEMETRY",
            carrier_status="ACCEPTED",
            sku="WH1000XM5-BLK-NEW",
            condition="NEW",
            color="silver",
        )
    ]
    eval_color = evaluate(receipt, None, ev_color_drift, now=datetime(2026, 12, 2, 12, 0, tzinfo=timezone.utc))
    assert eval_color.outcome == GateOutcome.DRIFT
    assert any(f.invariant_code == "INV-02-COLOR" for f in eval_color.findings)


def test_inv_03_carrier_label_only_causes_hold():
    receipt = create_mock_receipt()
    evidence = [
        FulfillmentEvidence(
            purchase_id="test-purchase-01",
            seq=1,
            source="carrier",
            external_event_id="EVT-01",
            trust_level="CARRIER_TELEMETRY",
            carrier_status="LABEL_CREATED",
            sku="WH1000XM5-BLK-NEW",
            condition="NEW",
            color="black",
        )
    ]
    eval_res = evaluate(receipt, None, evidence, now=datetime(2026, 12, 2, 12, 0, tzinfo=timezone.utc))
    assert eval_res.outcome == GateOutcome.HOLD
    assert eval_res.status_pill == "HOLD"
    assert eval_res.can_capture is False
    assert any(f.invariant_code == "INV-03-CARRIER" for f in eval_res.findings)


def test_inv_04_late_eta_causes_hold():
    receipt_created = datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc)
    receipt = create_mock_receipt(max_delivery_days=5, created_at=receipt_created)
    # ETA is 10 days out (past 5 day deadline)
    evidence = [
        FulfillmentEvidence(
            purchase_id="test-purchase-01",
            seq=1,
            source="carrier",
            external_event_id="EVT-01",
            trust_level="CARRIER_TELEMETRY",
            carrier_status="ACCEPTED",
            sku="WH1000XM5-BLK-NEW",
            condition="NEW",
            color="black",
            eta=receipt_created + timedelta(days=10),
        )
    ]
    eval_res = evaluate(receipt, None, evidence, now=datetime(2026, 12, 2, 12, 0, tzinfo=timezone.utc))
    assert eval_res.outcome == GateOutcome.HOLD
    assert eval_res.status_pill == "HOLD"
    assert any(f.invariant_code == "INV-04-ETA" for f in eval_res.findings)


def test_inv_05_merchant_claim_alone_cannot_satisfy_carrier():
    receipt = create_mock_receipt()
    evidence = [
        FulfillmentEvidence(
            purchase_id="test-purchase-01",
            seq=1,
            source="merchant",
            external_event_id="EVT-01",
            trust_level="MERCHANT_ATTESTATION",
            carrier_status="ACCEPTED",
            sku="WH1000XM5-BLK-NEW",
            condition="NEW",
            color="black",
        )
    ]
    eval_res = evaluate(receipt, None, evidence, now=datetime(2026, 12, 2, 12, 0, tzinfo=timezone.utc))
    assert eval_res.outcome == GateOutcome.HOLD
    assert any(f.invariant_code == "INV-05-TRUST" for f in eval_res.findings)


def test_inv_06_expired_authorization_causes_prohibited():
    receipt = create_mock_receipt()
    exp_time = datetime(2026, 12, 30, 12, 0, tzinfo=timezone.utc)
    auth = create_mock_auth(expiration_time=exp_time)
    # Happy path fulfillment evidence
    evidence = [
        FulfillmentEvidence(
            purchase_id="test-purchase-01",
            seq=1,
            source="carrier",
            external_event_id="EVT-01",
            trust_level="CARRIER_TELEMETRY",
            carrier_status="ACCEPTED",
            sku="WH1000XM5-BLK-NEW",
            condition="NEW",
            color="black",
        )
    ]

    # Evaluate AFTER expiration
    eval_res = evaluate(receipt, auth, evidence, now=exp_time + timedelta(hours=1))
    assert eval_res.outcome == GateOutcome.PROHIBITED
    assert eval_res.status_pill == "RENEWAL_REQUIRED"
    assert eval_res.can_capture is False
    assert any(f.invariant_code == "INV-06-EXPIRY" for f in eval_res.findings)


def test_all_invariants_pass_results_in_match():
    receipt = create_mock_receipt(
        expected_sku="WH1000XM5-BLK-NEW",
        expected_color="black",
        max_delivery_days=5,
        created_at=datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc),
    )
    auth = create_mock_auth(
        expiration_time=datetime(2026, 12, 30, 12, 0, tzinfo=timezone.utc),
        state="authorized",
    )
    evidence = [
        FulfillmentEvidence(
            purchase_id="test-purchase-01",
            seq=1,
            source="carrier",
            external_event_id="EVT-01",
            trust_level="CARRIER_TELEMETRY",
            carrier_status="ACCEPTED",
            sku="WH1000XM5-BLK-NEW",
            condition="NEW",
            color="black",
            eta=datetime(2026, 12, 3, 12, 0, tzinfo=timezone.utc),
        )
    ]
    eval_res = evaluate(receipt, auth, evidence, now=datetime(2026, 12, 2, 12, 0, tzinfo=timezone.utc))
    assert eval_res.outcome == GateOutcome.MATCH
    assert eval_res.status_pill == "AUTHORIZED · NOT CAPTURED"
    assert eval_res.can_capture is True
    assert "All promise invariants verified" in eval_res.explanation
