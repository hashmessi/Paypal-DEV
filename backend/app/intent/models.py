"""Pydantic schemas and typed models for Buyer Intent Constraints."""

from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class IntentConstraints(BaseModel):
    """Normalized, validated buyer purchase constraints."""

    product_type: str = Field(
        ...,
        description="Type or description of product (e.g. 'over-ear headphones')",
        json_schema_extra={"example": "over-ear headphones"},
    )
    condition: Literal["new", "refurbished", "any"] = Field(
        default="new",
        description="Required physical condition",
    )
    color: Optional[str] = Field(
        default=None,
        description="Requested color or finish",
        json_schema_extra={"example": "black"},
    )
    max_total_cents: int = Field(
        ...,
        description="Maximum total price in integer minor cents (e.g. 10000 for $100.00)",
        ge=1,
    )
    currency: str = Field(
        default="USD",
        max_length=3,
        description="ISO currency code (USD only for v1)",
    )
    deliver_within_days: int = Field(
        default=5,
        description="Relative delivery deadline in days",
        ge=1,
        le=60,
    )
    substitutions_allowed: bool = Field(
        default=False,
        description="Whether equivalent models are acceptable",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper != "USD":
            raise ValueError(f"Only USD is supported in v1, got: {v}")
        return v_upper


class ExtractedIntent(BaseModel):
    """Envelope returned from the Intent Extractor service."""

    constraints: IntentConstraints
    source: Literal["ai", "fallback"]
    instruction: str
    resolved_deadline: date
    instruction_hash: str

