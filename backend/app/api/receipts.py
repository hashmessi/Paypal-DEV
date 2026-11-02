"""Promise Receipt Compilation and Buyer Approval API endpoints."""

import json
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_clock
from app.core.clock import Clock
from app.core.db import get_db
from app.core.models import Purchase
from app.receipt.models import (
    ApproveReceiptRequest,
    BudgetExceededError,
    CompileReceiptRequest,
    PurchaseNotFoundError,
    StaleReceiptHashError,
)
from app.receipt.service import ReceiptService

router = APIRouter(prefix="/receipts", tags=["receipts"])


class ReceiptResponse(BaseModel):
    id: str
    purchase_id: str
    version: int
    status: str
    receipt_hash: str
    total_cents: int
    currency: str
    constraints: Dict[str, Any]
    product_snapshot: Dict[str, Any]
    merchant_quote: Dict[str, Any]
    capture_conditions: Dict[str, Any]
    approved_at: Any = None
    created_at: str


class ModifyTermsRequest(BaseModel):
    new_merchant_quote: Dict[str, Any]


@router.post("/compile", response_model=ReceiptResponse)
async def compile_receipt(
    req: CompileReceiptRequest,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
):
    """RCPT-01: Freeze constraints, snapshot, and merchant quote into canonical Promise Receipt.

    RCPT-02: Rejects compilation with 400 Bad Request if quote exceeds buyer budget.
    """
    service = ReceiptService(db=db, clock=clock)
    try:
        receipt = service.compile_receipt(
            purchase_id=req.purchase_id,
            constraints=req.constraints,
            product_snapshot=req.product_snapshot,
            merchant_quote=req.merchant_quote,
        )
        return ReceiptResponse(
            id=receipt.id,
            purchase_id=receipt.purchase_id,
            version=receipt.version,
            status=receipt.status,
            receipt_hash=receipt.receipt_hash,
            total_cents=receipt.total_cents,
            currency=receipt.currency,
            constraints=json.loads(receipt.constraints_json),
            product_snapshot=json.loads(receipt.product_snapshot_json),
            merchant_quote=json.loads(receipt.merchant_quote_json),
            capture_conditions=json.loads(receipt.capture_conditions_json),
            approved_at=receipt.approved_at.isoformat() if receipt.approved_at else None,
            created_at=receipt.created_at.isoformat(),
        )
    except BudgetExceededError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except PurchaseNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Receipt compilation failed: {str(err)}",
        )


@router.post("/{purchase_id}/approve", response_model=ReceiptResponse)
async def approve_receipt(
    purchase_id: str,
    req: ApproveReceiptRequest,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
):
    """RCPT-03: Buyer approves exact receipt hash before PayPal authorization.

    Returns HTTP 409 Conflict if attempting to approve a stale or non-current hash.
    """
    service = ReceiptService(db=db, clock=clock)
    try:
        receipt = service.approve_receipt(purchase_id=purchase_id, approved_hash=req.receipt_hash)
        return ReceiptResponse(
            id=receipt.id,
            purchase_id=receipt.purchase_id,
            version=receipt.version,
            status=receipt.status,
            receipt_hash=receipt.receipt_hash,
            total_cents=receipt.total_cents,
            currency=receipt.currency,
            constraints=json.loads(receipt.constraints_json),
            product_snapshot=json.loads(receipt.product_snapshot_json),
            merchant_quote=json.loads(receipt.merchant_quote_json),
            capture_conditions=json.loads(receipt.capture_conditions_json),
            approved_at=receipt.approved_at.isoformat() if receipt.approved_at else None,
            created_at=receipt.created_at.isoformat(),
        )
    except StaleReceiptHashError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.get("/{purchase_id}", response_model=ReceiptResponse)
async def get_receipt(
    purchase_id: str,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
):
    """Retrieve latest Promise Receipt for purchase."""
    service = ReceiptService(db=db, clock=clock)
    receipt = service.get_latest_receipt(purchase_id)
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No receipt found for purchase {purchase_id}")

    return ReceiptResponse(
        id=receipt.id,
        purchase_id=receipt.purchase_id,
        version=receipt.version,
        status=receipt.status,
        receipt_hash=receipt.receipt_hash,
        total_cents=receipt.total_cents,
        currency=receipt.currency,
        constraints=json.loads(receipt.constraints_json),
        product_snapshot=json.loads(receipt.product_snapshot_json),
        merchant_quote=json.loads(receipt.merchant_quote_json),
        capture_conditions=json.loads(receipt.capture_conditions_json),
        approved_at=receipt.approved_at.isoformat() if receipt.approved_at else None,
        created_at=receipt.created_at.isoformat(),
    )


@router.post("/{purchase_id}/modify-terms", response_model=ReceiptResponse)
async def modify_merchant_terms(
    purchase_id: str,
    req: ModifyTermsRequest,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
):
    """RCPT-04: Merchant modifies terms. Marks prior receipt STALE and compiles next version."""
    service = ReceiptService(db=db, clock=clock)
    try:
        new_receipt = service.handle_merchant_term_change(
            purchase_id=purchase_id,
            new_merchant_quote=req.new_merchant_quote,
        )
        return ReceiptResponse(
            id=new_receipt.id,
            purchase_id=new_receipt.purchase_id,
            version=new_receipt.version,
            status=new_receipt.status,
            receipt_hash=new_receipt.receipt_hash,
            total_cents=new_receipt.total_cents,
            currency=new_receipt.currency,
            constraints=json.loads(new_receipt.constraints_json),
            product_snapshot=json.loads(new_receipt.product_snapshot_json),
            merchant_quote=json.loads(new_receipt.merchant_quote_json),
            capture_conditions=json.loads(new_receipt.capture_conditions_json),
            approved_at=new_receipt.approved_at.isoformat() if new_receipt.approved_at else None,
            created_at=new_receipt.created_at.isoformat(),
        )
    except BudgetExceededError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except PurchaseNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
