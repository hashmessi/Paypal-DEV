"""Pytest fixtures for PromiseLoop backend test suite."""

from datetime import datetime, timezone
import sys
from pathlib import Path
from typing import Callable, Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend directory is in sys.path
backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.api.deps import get_clock, get_db, get_gateway
from app.core.clock import FixedClock
from app.core.models import Base, FulfillmentEvidence, PromiseReceipt
from app.main import app
from app.payments.fake import FakeGateway


@pytest.fixture
def fixed_now() -> datetime:
    return datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def fixed_clock(fixed_now: datetime) -> FixedClock:
    return FixedClock(fixed_now)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide isolated in-memory SQLite database session for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def fake_gateway() -> FakeGateway:
    return FakeGateway()


@pytest.fixture
def bind_receipt(db_session: Session, fixed_now: datetime) -> Callable[[str, int], None]:
    """Attach an approved Promise Receipt and carrier evidence so the gate can return MATCH."""

    def _bind(purchase_id: str, total_cents: int) -> None:
        db_session.add(
            PromiseReceipt(
                purchase_id=purchase_id,
                version=1,
                status="active",
                receipt_hash="0" * 64,
                canonical_payload="{}",
                constraints_json="{}",
                product_snapshot_json="{}",
                merchant_quote_json="{}",
                capture_conditions_json="{}",
                total_cents=total_cents,
                currency="USD",
                created_at=fixed_now,
            )
        )
        db_session.add(
            FulfillmentEvidence(
                purchase_id=purchase_id,
                seq=1,
                source="carrier",
                external_event_id="EVT-BIND-1",
                trust_level="CARRIER_TELEMETRY",
                carrier_status="ACCEPTED",
                raw_payload="{}",
                recorded_at=fixed_now,
            )
        )
        db_session.commit()

    return _bind


@pytest.fixture
def client(db_session: Session, fake_gateway: FakeGateway, fixed_clock: FixedClock) -> Generator[TestClient, None, None]:
    """TestClient with dependency overrides for isolated tests."""
    def override_get_db():
        yield db_session

    def override_get_gateway():
        return fake_gateway

    def override_get_clock():
        return fixed_clock

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_gateway] = override_get_gateway
    app.dependency_overrides[get_clock] = override_get_clock

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

