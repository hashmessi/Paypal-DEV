"""Product Discovery and Merchant Quote API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.discovery.adapter import Channel3Adapter
from app.discovery.models import (
    CurrencyNotSupportedError,
    MerchantQuote,
    ProductCandidate,
)

router = APIRouter(prefix="/discovery", tags=["discovery"])
discovery_adapter = Channel3Adapter()


class QuoteRequest(BaseModel):
    offer_id: str = Field(..., description="Selected offer ID")
    custom_price_cents: Optional[int] = Field(None, description="Optional custom price override", ge=1)
    custom_shipping_cents: Optional[int] = Field(None, description="Optional custom shipping override", ge=0)


@router.get("/search", response_model=List[ProductCandidate])
async def search_products(
    q: str = Query("headphones", description="Search query term"),
):
    """DISC-01: Search product candidates via Channel3 adapter with demo fallback."""
    results = await discovery_adapter.search(query=q)
    return results


@router.post("/quote", response_model=MerchantQuote)
async def generate_quote(req: QuoteRequest):
    """DISC-03: Generate confirmed merchant quote labeled 'Sandbox stand-in for <domain>'.

    DISC-02: Rejects non-USD offers with 400 Bad Request.
    """
    try:
        quote = discovery_adapter.generate_merchant_quote(
            offer_id=req.offer_id,
            custom_price_cents=req.custom_price_cents,
            custom_shipping_cents=req.custom_shipping_cents,
        )
        return quote
    except CurrencyNotSupportedError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quote generation failed: {str(err)}",
        )

