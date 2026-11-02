"""Request guards: admin token for seed endpoints, per-IP rate limit for LLM endpoints (SEC-03)."""

import hmac
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Header, HTTPException, Request, status

from app.core.config import settings

_hits: Dict[str, Deque[float]] = defaultdict(deque)


def require_admin(x_admin_token: str = Header(default="")) -> None:
    """Fail closed: with no ADMIN_TOKEN configured, admin endpoints are unreachable."""
    expected = settings.ADMIN_TOKEN
    if not expected or not hmac.compare_digest(x_admin_token.encode(), expected.encode()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin token required")


def rate_limit_llm(request: Request) -> None:
    """Sliding 60s window per client IP. shortcut: in-process memory, single instance only; use Redis if scaled out."""
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= settings.LLM_RATE_LIMIT_PER_MIN:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )
    q.append(now)
