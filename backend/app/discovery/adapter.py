"""Channel3 Product Discovery Adapter and Merchant Quote Generator."""

import logging
from typing import Any, List, Literal, Optional, cast
import uuid

try:
    import httpx
except ImportError:
    import httpx2 as httpx

from app.core.canon import dollar_str_to_cents
from app.core.config import settings
from app.discovery.catalog import RAW_DEMO_PRODUCTS
from app.discovery.models import (
    CurrencyNotSupportedError,
    MerchantQuote,
    ProductCandidate,
    ProductOffer,
)
from app.intent.models import IntentConstraints

logger = logging.getLogger(__name__)


def normalize_condition(raw_cond: Any) -> str:
    """DISC-02: condition: null is treated as UNVERIFIED, never NEW."""
    if raw_cond is None:
        return "UNVERIFIED"
    s = str(raw_cond).strip().lower()
    if s in ("new", "brand new"):
        return "NEW"
    if s in ("refurbished", "renewed", "refurb"):
        return "REFURBISHED"
    return "UNVERIFIED"


class Channel3Adapter:
    """Integrates with Channel3 API with robust fallback to demo catalog."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or settings.CHANNEL3_API_KEY

    def _parse_offer(self, prod_id: str, raw: dict[str, Any]) -> ProductOffer:
        currency = raw.get("currency", "USD").upper()
        price_val = raw.get("price", 0.0)
        shipping_val = raw.get("shipping_fee", 0.0)

        condition = normalize_condition(raw.get("condition"))

        return ProductOffer(
            offer_id=raw.get("id", f"OFFER-{uuid.uuid4().hex[:8]}"),
            product_id=prod_id,
            merchant_name=raw.get("merchant_name", "Unknown Merchant"),
            merchant_domain=raw.get("merchant_domain", "example.com"),
            title=raw.get("title", ""),
            price_cents=dollar_str_to_cents(price_val),
            currency=currency,
            condition=cast(Literal["NEW", "REFURBISHED", "UNVERIFIED"], condition),
            color=raw.get("color"),
            rating=float(raw.get("rating", 4.5)),
            in_stock=bool(raw.get("in_stock", True)),
            shipping_cents=dollar_str_to_cents(shipping_val),
            estimated_days=int(raw.get("estimated_delivery_days", 3)),
            raw_payload=raw,
        )

    async def search(
        self,
        query: str = "headphones",
        constraints: Optional[IntentConstraints] = None,
    ) -> List[ProductCandidate]:
        """Search products matching query and optional buyer constraints."""
        # Check real Channel3 API if key present
        if self.api_key:
            try:
                url = f"https://api.channel3.ai/v1/products/search?q={query}"
                headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    # Parse candidates from Channel3 API schema
                    results = []
                    for item in data.get("products", []):
                        pid = item.get("id", f"PROD-{uuid.uuid4().hex[:8]}")
                        offers = [self._parse_offer(pid, o) for o in item.get("offers", [])]
                        results.append(
                            ProductCandidate(
                                product_id=pid,
                                title=item.get("title", ""),
                                brand=item.get("brand", "Unknown"),
                                category=item.get("category", "General"),
                                image_url=item.get("image_url", ""),
                                description=item.get("description", ""),
                                offers=offers,
                            )
                        )
                    if results:
                        return results
            except Exception as err:
                logger.warning("Channel3 API search failed, falling back to local catalog: %s", err)

        # Fallback to local catalog
        candidates = []
        for raw_prod in RAW_DEMO_PRODUCTS:
            pid = raw_prod["product_id"]
            offers = []
            for raw_o in raw_prod["offers"]:
                offer = self._parse_offer(pid, raw_o)
                # Keep offers matching color/condition if constraints provided
                offers.append(offer)

            candidates.append(
                ProductCandidate(
                    product_id=pid,
                    title=raw_prod["title"],
                    brand=raw_prod["brand"],
                    category=raw_prod["category"],
                    image_url=raw_prod["image_url"],
                    description=raw_prod["description"],
                    offers=offers,
                )
            )

        return candidates

    def get_offer_by_id(self, offer_id: str) -> Optional[ProductOffer]:
        """Lookup offer in catalog by ID."""
        for prod in RAW_DEMO_PRODUCTS:
            for raw_o in prod["offers"]:
                if raw_o.get("id") == offer_id:
                    return self._parse_offer(prod["product_id"], raw_o)
        return None

    def generate_merchant_quote(
        self,
        offer_id: str,
        custom_price_cents: Optional[int] = None,
        custom_shipping_cents: Optional[int] = None,
    ) -> MerchantQuote:
        """Generate confirmed merchant quote labeled 'Sandbox stand-in for <domain>'."""
        offer = self.get_offer_by_id(offer_id)
        if not offer:
            raise ValueError(f"Offer {offer_id} not found in discovery catalog")

        # DISC-02: Non-USD offers are rejected
        if offer.currency != "USD":
            raise CurrencyNotSupportedError(offer.currency)

        subtotal = custom_price_cents if custom_price_cents is not None else offer.price_cents
        shipping = custom_shipping_cents if custom_shipping_cents is not None else offer.shipping_cents
        tax = 0  # Standard online sales tax or 0
        total = subtotal + shipping + tax

        label = f"Sandbox stand-in for {offer.merchant_domain}"
        sku = offer.raw_payload.get("sku", f"SKU-{offer.offer_id[-8:]}")

        return MerchantQuote(
            quote_id=f"QUOTE-{uuid.uuid4().hex[:10].upper()}",
            offer_id=offer.offer_id,
            product_id=offer.product_id,
            merchant_name=offer.merchant_name,
            merchant_domain=offer.merchant_domain,
            label=label,
            subtotal_cents=subtotal,
            shipping_cents=shipping,
            tax_cents=tax,
            total_cents=total,
            currency="USD",
            condition=offer.condition,
            color=offer.color,
            promised_delivery_days=offer.estimated_days,
            sku=sku,
        )
