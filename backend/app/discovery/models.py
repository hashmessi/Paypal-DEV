"""Data models for Product Discovery and Merchant Quotes."""

from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field


class DiscoveryError(Exception):
    """Base exception for product discovery."""
    pass


class CurrencyNotSupportedError(DiscoveryError):
    """Raised when an offer is in a non-USD currency."""
    def __init__(self, currency: str) -> None:
        super().__init__(f"Non-USD currency '{currency}' is not supported in v1. Only USD is accepted.")


class ProductOffer(BaseModel):
    offer_id: str
    product_id: str
    merchant_name: str
    merchant_domain: str
    title: str
    price_cents: int
    currency: str
    condition: Literal["NEW", "REFURBISHED", "UNVERIFIED"]
    color: Optional[str] = None
    rating: float = 4.8
    in_stock: bool = True
    shipping_cents: int = 0
    estimated_days: int = 3
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class ProductCandidate(BaseModel):
    product_id: str
    title: str
    brand: str
    category: str
    image_url: str
    description: str
    offers: List[ProductOffer]


class MerchantQuote(BaseModel):
    quote_id: str
    offer_id: str
    product_id: str
    merchant_name: str
    merchant_domain: str
    label: str  # "Sandbox stand-in for <domain>"
    subtotal_cents: int
    shipping_cents: int
    tax_cents: int
    total_cents: int
    currency: str
    condition: Literal["NEW", "REFURBISHED", "UNVERIFIED"]
    color: Optional[str] = None
    promised_delivery_days: int = 3
    sku: str = "WH-1000XM5-BLK"

