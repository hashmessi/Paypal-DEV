"""Payments module providing state machine, ports, fake adapter, and PayPal adapter."""

from app.payments.state import (
    PaymentState,
    IllegalStateTransitionError,
    TerminalStateError,
    is_terminal,
    validate_transition,
)

__all__ = [
    "PaymentState",
    "IllegalStateTransitionError",
    "TerminalStateError",
    "is_terminal",
    "validate_transition",
]

