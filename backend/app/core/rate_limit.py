"""Lightweight in-process rate limiting for auth endpoints.

A dependency-free sliding-window counter. We deliberately avoid slowapi/Redis:
Cloud Run runs a small number of instances and each limiter is per-instance, so
an external store would add ops surface for marginal gain at this scale. The
per-account (email) dimension is the one that actually stops a password brute
force against a known target — it is not IP-spoofable — while the per-IP
dimension is defense-in-depth.

Caveat (documented on purpose): per-instance memory means the effective limit is
`limit * instance_count`, and the per-IP key trusts the left-most
`X-Forwarded-For` entry, which a client can spoof. Neither weakens the per-email
guard, which is the primary control.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_s: float) -> None:
        self._limit = limit
        self._window = window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        """Record one hit for ``key``; raise 429 if it exceeds the window."""
        now = time.monotonic()
        cutoff = now - self._window
        dq = self._hits[key]
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= self._limit:
            retry_after = int(dq[0] + self._window - now) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Please wait and try again.",
                headers={"Retry-After": str(retry_after)},
            )
        dq.append(now)
        self._maybe_sweep(cutoff)

    def _maybe_sweep(self, cutoff: float) -> None:
        # Bound memory: once the key set grows large, drop buckets whose most
        # recent hit has aged out. Cheap and amortized — only fires when the
        # dict is big enough to matter.
        if len(self._hits) <= 4096:
            return
        stale = [k for k, dq in self._hits.items() if not dq or dq[-1] < cutoff]
        for k in stale:
            del self._hits[k]


def client_ip(request: Request) -> str:
    """Best-effort client IP. Left-most XFF entry (spoofable — used only as a
    secondary, defense-in-depth dimension), falling back to the socket peer."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else "unknown"


# Shared limiters. Windows are 60s; limits are generous enough not to bother a
# real user retrying a typo, tight enough to make automated guessing useless.
login_ip_limiter = SlidingWindowLimiter(limit=20, window_s=60.0)
login_account_limiter = SlidingWindowLimiter(limit=8, window_s=60.0)
refresh_ip_limiter = SlidingWindowLimiter(limit=40, window_s=60.0)
otp_verify_limiter = SlidingWindowLimiter(limit=10, window_s=60.0)
otp_request_ip_limiter = SlidingWindowLimiter(limit=8, window_s=60.0)
