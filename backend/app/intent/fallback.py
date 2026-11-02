"""Deterministic rule-based intent parser for zero-key offline fallback."""

import re
from typing import Optional

from app.core.canon import dollar_str_to_cents
from app.intent.models import IntentConstraints

KNOWN_COLORS = [
    "black", "white", "silver", "gray", "grey", "blue", "red", "gold", "midnight", "graphite"
]


def extract_fallback_constraints(instruction: str) -> IntentConstraints:
    """Parse natural language instruction into strict typed constraints using regex patterns."""
    text = instruction.lower().strip()

    # 1. Condition extraction
    condition = "new"
    if re.search(r"\b(refurbished|renewed|refurb)\b", text):
        condition = "refurbished"
    elif re.search(r"\b(used|pre-owned|any)\b", text):
        condition = "any"
    elif re.search(r"\b(brand\s*new|new)\b", text):
        condition = "new"

    # 2. Price extraction
    # Matches: 'under $100', 'under 100', 'max $89.99', 'under $100.00'
    price_match = re.search(r"(?:under|below|max|maximum|less than|up to)\s*\$?(\d+(?:\.\d{1,2})?)", text)
    if not price_match:
        price_match = re.search(r"\$(\d+(?:\.\d{1,2})?)", text)

    if price_match:
        max_cents = dollar_str_to_cents(price_match.group(1))
    else:
        max_cents = 10000  # Default $100.00

    # 3. Color extraction
    found_color: Optional[str] = None
    for color in KNOWN_COLORS:
        if re.search(rf"\b{color}\b", text):
            found_color = color
            break

    # 4. Delivery window extraction (in days)
    # Matches: 'within 5 days', 'in 3 days', 'arrive within 5 days', '5 days'
    delivery_match = re.search(r"(?:within|in|arrive in|deliver within|deliver in)\s*(\d+)\s*(?:business\s*)?days?", text)
    if not delivery_match:
        delivery_match = re.search(r"(\d+)\s*days?", text)

    days = int(delivery_match.group(1)) if delivery_match else 5
    if days < 1:
        days = 1
    elif days > 60:
        days = 60

    # 5. Substitution
    subs_allowed = bool(re.search(r"\b(substitut\w+|equivalent|alternat\w+)\s*(?:allowed|ok|permitted|fine|yes)\b", text))

    # 6. Product type clean-up
    # Extract noun phrase by stripping common intent keywords
    cleaned = re.sub(
        r"(?:brand\s*new|new|refurbished|renewed|used|under\s*\$?\d+(?:\.\d+)?|\$\d+(?:\.\d+)?|within\s*\d+\s*days?|in\s*\d+\s*days?|arrive\s*within\s*\d+\s*days?|please|buy|find|get|order|deliver|me|a|an|the|with|and|,)",
        " ",
        text,
    )
    if found_color:
        cleaned = re.sub(rf"\b{found_color}\b", " ", cleaned)

    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]
    product_type = " ".join(tokens) if tokens else "over-ear headphones"
    if "headphone" in text and "headphone" not in product_type:
        product_type = "over-ear headphones"

    return IntentConstraints(
        product_type=product_type,
        condition=condition,
        color=found_color,
        max_total_cents=max_cents,
        currency="USD",
        deliver_within_days=days,
        substitutions_allowed=subs_allowed,
    )

