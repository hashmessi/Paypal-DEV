"""SQLAlchemy declarative models for PromiseLoop."""

from datetime import datetime, timezone
import uuid
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    ref: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    buyer_instruction: Mapped[str] = mapped_column(Text, nullable=False)
    receipt_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    authorizations: Mapped[list["PaymentAuthorization"]] = relationship(
        "PaymentAuthorization", back_populates="purchase", cascade="all, delete-orphan"
    )
    events: Mapped[list["DecisionEvent"]] = relationship(
        "DecisionEvent", back_populates="purchase", cascade="all, delete-orphan"
    )
    receipts: Mapped[list["PromiseReceipt"]] = relationship(
        "PromiseReceipt", back_populates="purchase", cascade="all, delete-orphan"
    )
    evidence: Mapped[list["FulfillmentEvidence"]] = relationship(
        "FulfillmentEvidence", back_populates="purchase", cascade="all, delete-orphan"
    )
    gate_evaluations: Mapped[list["GateEvaluationRecord"]] = relationship(
        "GateEvaluationRecord", back_populates="purchase", cascade="all, delete-orphan"
    )


class PaymentAuthorization(Base):
    __tablename__ = "payment_authorizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    purchase_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchases.id"), nullable=False)
    order_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    authorization_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    state: Mapped[str] = mapped_column(String(32), default="created", nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    expiration_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    honor_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    capture_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    void_reason: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="authorizations")


class FinancialAction(Base):
    __tablename__ = "financial_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    authorization_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)  # 'capture' | 'void'
    request_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # 'pending' | 'completed' | 'failed'
    response_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("authorization_id", "action", name="uq_auth_action"),
    )


class DecisionEvent(Base):
    """Append-only, hash-chained ledger event table."""
    __tablename__ = "decision_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    purchase_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchases.id"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # Canonical JSON
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="events")

    __table_args__ = (
        UniqueConstraint("purchase_id", "seq", name="uq_purchase_event_seq"),
    )


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    resource_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    raw_body: Mapped[str] = mapped_column(Text, nullable=False)
    headers: Mapped[str] = mapped_column(Text, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PromiseReceipt(Base):
    """Canonical, versioned Promise Receipt sealing constraints, product snapshot, and merchant quote."""
    __tablename__ = "promise_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    purchase_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchases.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)  # 'draft' | 'approved' | 'stale' | 'superseded'
    receipt_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    canonical_payload: Mapped[str] = mapped_column(Text, nullable=False)
    constraints_json: Mapped[str] = mapped_column(Text, nullable=False)
    product_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    merchant_quote_json: Mapped[str] = mapped_column(Text, nullable=False)
    capture_conditions_json: Mapped[str] = mapped_column(Text, nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="receipts")

    __table_args__ = (
        UniqueConstraint("purchase_id", "version", name="uq_purchase_receipt_version"),
    )


class ExtractionCache(Base):
    """Cache table for natural-language instruction extractions to avoid redundant LLM invocations."""
    __tablename__ = "extraction_cache"

    instruction_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    instruction_text: Mapped[str] = mapped_column(Text, nullable=False)
    constraints_json: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # 'ai' | 'fallback'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)



class FulfillmentEvidence(Base):
    """Ingested fulfillment evidence from carrier telemetry or merchant attestations (FULF-01)."""
    __tablename__ = "fulfillment_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    purchase_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchases.id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)  # 'carrier' | 'merchant' | 'synthetic_console'
    external_event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    trust_level: Mapped[str] = mapped_column(String(32), default="CARRIER_TELEMETRY", nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    carrier_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # 'LABEL_CREATED' | 'ACCEPTED' | 'IN_TRANSIT' | 'DELIVERED'
    sku: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    condition: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # 'NEW' | 'REFURBISHED' | 'UNVERIFIED'
    color: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    eta: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="evidence")

    __table_args__ = (
        UniqueConstraint("purchase_id", "source", "external_event_id", name="uq_evidence_dedup"),
    )


class GateEvaluationRecord(Base):
    """Audit log of deterministic gate decisions evaluating fulfillment against Promise Receipt."""
    __tablename__ = "gate_evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    purchase_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchases.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)  # 'MATCH' | 'DRIFT' | 'HOLD' | 'PROHIBITED'
    status_pill: Mapped[str] = mapped_column(String(64), nullable=False)  # 'AUTHORIZED · NOT CAPTURED' | 'CAPTURE BLOCKED' | 'CAPTURED' | 'HOLD' | 'RENEWAL_REQUIRED'
    findings_json: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    purchase: Mapped["Purchase"] = relationship("Purchase", back_populates="gate_evaluations")
