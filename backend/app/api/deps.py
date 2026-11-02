"""FastAPI dependencies for Database, PaymentGateway, and Clock."""

from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock, SystemClock
from app.core.db import get_db
from app.payments.fake import FakeGateway
from app.payments.port import PaymentGateway
from app.payments.paypal import PayPalGateway
from app.proof.counterfactual import gateway_is_simulated

# Global singleton fake gateway for test / demo environment
_fake_gateway_singleton = FakeGateway()


def get_clock() -> Clock:
    """Return default system clock."""
    return SystemClock()


def get_gateway() -> PaymentGateway:
    """Provide PayPalGateway in live/sandbox, or FakeGateway if test credentials."""
    if gateway_is_simulated():
        return _fake_gateway_singleton
    return PayPalGateway()

