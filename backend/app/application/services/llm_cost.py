"""LLM cost estimation for admin telemetry.

Prices are per **1M tokens**. Groq numbers are from their public
pricing page (current as of 2026-07); OpenAI numbers are OpenAI's
public list. Unknown models fall back to (0, 0) so we still capture
tokens but leave cost blank rather than lying about it.

This is intentionally a static lookup table — pricing changes rarely
and drifts by tenths of a percent between refreshes; the admin panel
would rather show a stable "here's the ballpark" than nothing at all.
Update the numbers when you notice they've moved materially.
"""
from __future__ import annotations

from typing import Any

# (input_per_1m_usd, output_per_1m_usd)
_MODEL_PRICES: dict[str, tuple[float, float]] = {
    # Groq — hosts OSS Llama + gpt-oss models cheaply.
    "openai/gpt-oss-120b": (0.15, 0.60),
    "openai/gpt-oss-20b":  (0.05, 0.20),
    "llama-3.1-70b-versatile": (0.59, 0.79),
    "llama-3.1-8b-instant":    (0.05, 0.08),
    "llama-3.3-70b-versatile": (0.59, 0.79),
    # OpenAI proper.
    "gpt-4o-mini":  (0.15, 0.60),
    "gpt-4o":       (2.50, 10.0),
    "gpt-4-turbo":  (10.0, 30.0),
}


def estimate_cost_usd(
    model: str | None,
    prompt_tokens: int,
    completion_tokens: int,
) -> float | None:
    """Return the estimated USD cost of one call, or None if unknown model."""
    if not model:
        return None
    price = _MODEL_PRICES.get(model)
    if price is None:
        return None
    in_rate, out_rate = price
    return round(
        (prompt_tokens * in_rate + completion_tokens * out_rate) / 1_000_000,
        6,
    )


def usage_meta(
    *,
    usage: dict[str, int] | None,
    model: str | None,
    provider: str | None,
) -> dict[str, Any]:
    """Convert an AIRawResponse's usage snapshot into meta fields.

    Fields (all optional — absent when the provider didn't report them):
        prompt_tokens, completion_tokens, total_tokens, model,
        provider, cost_usd (nullable when the model isn't in the
        price table).
    """
    if not usage:
        return {}
    meta: dict[str, Any] = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        v = usage.get(key)
        if isinstance(v, int):
            meta[key] = v
    if model:
        meta["model"] = model
    if provider:
        meta["provider"] = provider
    cost = estimate_cost_usd(
        model,
        usage.get("prompt_tokens", 0),
        usage.get("completion_tokens", 0),
    )
    if cost is not None:
        meta["cost_usd"] = cost
    return meta
