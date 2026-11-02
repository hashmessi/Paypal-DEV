"""Tests for Payment State Machine and Transition Rules (PAY-04)."""

import pytest

from app.payments.state import (
    IllegalStateTransitionError,
    PaymentState,
    TerminalStateError,
    is_terminal,
    validate_transition,
)


def test_valid_transitions():
    """Verify standard happy-path and cancellation transitions are accepted."""
    validate_transition(PaymentState.CREATED, PaymentState.APPROVED)
    validate_transition(PaymentState.CREATED, PaymentState.AUTHORIZED)
    validate_transition(PaymentState.CREATED, PaymentState.VOIDED)
    validate_transition(PaymentState.APPROVED, PaymentState.AUTHORIZED)
    validate_transition(PaymentState.APPROVED, PaymentState.VOIDED)
    validate_transition(PaymentState.AUTHORIZED, PaymentState.CAPTURING)
    validate_transition(PaymentState.CAPTURING, PaymentState.CAPTURED)
    validate_transition(PaymentState.AUTHORIZED, PaymentState.VOIDED)
    validate_transition(PaymentState.AUTHORIZED, PaymentState.EXPIRED)
    validate_transition(PaymentState.CAPTURING, PaymentState.AUTHORIZED)  # transient retry rollback


def test_idempotent_self_transitions():
    """Verify asserting same state does not raise."""
    validate_transition(PaymentState.AUTHORIZED, PaymentState.AUTHORIZED)
    validate_transition(PaymentState.CAPTURED, PaymentState.CAPTURED)


def test_terminal_states_identification():
    """Verify exact terminal states."""
    assert is_terminal(PaymentState.CAPTURED) is True
    assert is_terminal(PaymentState.VOIDED) is True
    assert is_terminal(PaymentState.EXPIRED) is True
    assert is_terminal(PaymentState.FAILED) is True

    assert is_terminal(PaymentState.CREATED) is False
    assert is_terminal(PaymentState.APPROVED) is False
    assert is_terminal(PaymentState.AUTHORIZED) is False
    assert is_terminal(PaymentState.CAPTURING) is False


@pytest.mark.parametrize(
    "curr,target",
    [
        (PaymentState.CAPTURED, PaymentState.CAPTURING),
        (PaymentState.CAPTURED, PaymentState.VOIDED),
        (PaymentState.CAPTURED, PaymentState.AUTHORIZED),
        (PaymentState.VOIDED, PaymentState.AUTHORIZED),
        (PaymentState.VOIDED, PaymentState.CAPTURED),
        (PaymentState.EXPIRED, PaymentState.CAPTURING),
        (PaymentState.EXPIRED, PaymentState.CAPTURED),
        (PaymentState.FAILED, PaymentState.CAPTURING),
        (PaymentState.CREATED, PaymentState.CAPTURED),
    ],
)
def test_illegal_transitions_raise_error(curr: str, target: str):
    """Enforce that illegal transitions raise IllegalStateTransitionError."""
    with pytest.raises(IllegalStateTransitionError) as exc_info:
        validate_transition(curr, target)
    assert exc_info.value.current_state == curr
    assert exc_info.value.target_state == target


def test_terminal_state_error_exception():
    err = TerminalStateError(PaymentState.CAPTURED.value, "capture")
    assert "Cannot perform 'capture' on authorization in terminal state 'captured'" in str(err)
