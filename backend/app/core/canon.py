"""Canonical JSON and cryptographic hashing utilities.

Implements RFC 8785 (JSON Canonicalization Scheme - JCS) formatting:
- Keys sorted lexicographically
- No whitespace separators (',' and ':')
- UTF-8 encoding without ASCII escaping
- Strict integer minor unit serialization for money
"""

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Union


def to_utc_iso(dt: datetime) -> str:
    """Format datetime as canonical ISO 8601 UTC string (e.g. 2026-11-01T12:00:00Z)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    ms = f".{dt.microsecond:06d}" if dt.microsecond else ""
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + ms + "Z"


def canonical_json(data: Any) -> str:
    """Serialize Python object to RFC 8785-compliant canonical JSON."""
    if data is None or isinstance(data, (bool, int, float, str)):
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    if isinstance(data, (list, tuple)):
        items = [canonical_json(item) for item in data]
        return "[" + ",".join(items) + "]"

    if isinstance(data, dict):
        sorted_keys = sorted(data.keys())
        items = [
            json.dumps(str(k), ensure_ascii=False) + ":" + canonical_json(data[k])
            for k in sorted_keys
        ]
        return "{" + ",".join(items) + "}"

    if isinstance(data, Decimal):
        # Format decimal with exact two fraction digits for currency
        return json.dumps(str(data.quantize(Decimal("0.01"))), ensure_ascii=False)

    # Fallback to dict if dataclass or pydantic model
    if hasattr(data, "model_dump"):
        return canonical_json(data.model_dump())
    if hasattr(data, "__dict__"):
        return canonical_json(data.__dict__)

    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def sha256_hex(data: Union[str, bytes, Any]) -> str:
    """Calculate SHA-256 digest in lowercase hexadecimal format."""
    if isinstance(data, bytes):
        raw = data
    elif isinstance(data, str):
        raw = data.encode("utf-8")
    else:
        raw = canonical_json(data).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


def cents_to_dollar_str(cents: int) -> str:
    """Convert integer minor cents to two-decimal dollar string (e.g. 8999 -> '89.99')."""
    if not isinstance(cents, int):
        raise TypeError(f"Cents must be integer minor units, got {type(cents).__name__}")
    dollars = Decimal(cents) / Decimal(100)
    return str(dollars.quantize(Decimal("0.01")))


def dollar_str_to_cents(dollars: Union[str, Decimal, int, float]) -> int:
    """Convert dollar representation to integer minor cents (e.g. '89.99' -> 8999)."""
    if isinstance(dollars, int):
        return dollars * 100
    dec = Decimal(str(dollars))
    return int((dec * Decimal(100)).quantize(Decimal("1")))
