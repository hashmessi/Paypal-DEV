"""Payment state machine and transition validation.

Enforces deterministic lifecycle transitions for authorizations and captures.
Terminal states (captured, voided, expired, failed) are immutable.
"""

from enum import Enum
from typing import Set


class PaymentState(str, Enum):
    CREATED = "created"
    APPROVED = "approved"
    AUTHORIZED = "authorized"
    CAPTURING = "capturing"
    CAPTURED = "captured"
    VOIDED = "voided"
    EXPIRED = "expired"
    FAILED = "failed"


TERMINAL_STATES: Set[PaymentState] = {
    PaymentState.CAPTURED,
    PaymentState.VOIDED,
    PaymentState.EXPIRED,
    PaymentState.FAILED,
}

LEGAL_TRANSITIONS: dict[PaymentState, Set[PaymentState]] = {
    PaymentState.CREATED: {
        PaymentState.APPROVED,
        PaymentState.AUTHORIZED,
        PaymentState.VOIDED,
        PaymentState.FAILED,
    },
    PaymentState.APPROVED: {
        PaymentState.AUTHORIZED,
        PaymentState.VOIDED,
        PaymentState.FAILED,
    },
    PaymentState.AUTHORIZED: {
        PaymentState.CAPTURING,
        PaymentState.VOIDED,
        PaymentState.EXPIRED,
        PaymentState.FAILED,
    },
    PaymentState.CAPTURING: {
        PaymentState.CAPTURED,
        PaymentState.FAILED,
        PaymentState.AUTHORIZED,  # Rollback on transient retryable failure
    },
    PaymentState.CAPTURED: set(),
    PaymentState.VOIDED: set(),
    PaymentState.EXPIRED: set(),
    PaymentState.FAILED: set(),
}


class PaymentStateError(Exception):
    """Base exception for payment state machine errors."""
    pass


class IllegalStateTransitionError(PaymentStateError):
    """Raised when an illegal state transition is attempted."""

    def __init__(self, current_state: str, target_state: str, message: str = "") -> None:
        self.current_state = current_state
        self.target_state = target_state
        detail = message or f"Illegal transition from '{current_state}' to '{target_state}'"
        super().__init__(detail)


class TerminalStateError(PaymentStateError):
    """Raised when an action is attempted on an authorization in a terminal state."""

    def __init__(self, current_state: str, action: str) -> None:
        self.current_state = current_state
        self.action = action
        super().__init__(f"Cannot perform '{action}' on authorization in terminal state '{current_state}'")


class CaptureBlockedByGateError(PaymentStateError):
    """Raised when capture is blocked by drift or invariant gate failure (PAY-02)."""

    def __init__(self, message: str, outcome: str = "", findings: list | None = None) -> None:
        self.outcome = outcome
        self.findings = findings or []
        super().__init__(message)


def is_terminal(state: str) -> bool:
    """Return whether state is terminal."""
    try:
        enum_state = PaymentState(state)
        return enum_state in TERMINAL_STATES
    except ValueError:
        return False


def validate_transition(current_state: str, target_state: str) -> None:
    """Validate whether transitioning from current_state to target_state is legal.

    Raises:
        IllegalStateTransitionError: if the transition is not allowed.
    """
    try:
        curr = PaymentState(current_state)
    except ValueError:
        raise IllegalStateTransitionError(current_state, target_state, f"Invalid current state: '{current_state}'")

    try:
        target = PaymentState(target_state)
    except ValueError:
        raise IllegalStateTransitionError(current_state, target_state, f"Invalid target state: '{target_state}'")

    if curr == target:
        # Idempotent state re-assertion is allowed
        return

    allowed = LEGAL_TRANSITIONS.get(curr, set())
    if target not in allowed:
        raise IllegalStateTransitionError(current_state, target_state)
