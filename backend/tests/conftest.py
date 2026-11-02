"""Pytest fixtures for PromiseLoop backend test suite."""

from datetime import datetime, timezone
import sys
from pathlib import Path
from typing import Generator
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
from app.core.models import Base
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

