"""Fetch a public URL and reduce it to readable plain text.

Defensive defaults: short timeout, redirect cap, custom UA, size cap. Not an
SSRF guard — the app is single-user; we trust the operator not to point this
at internal hosts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

DEFAULT_TIMEOUT_S = 12.0
MAX_BYTES = 1_500_000  # ~1.5 MB cap on the raw HTML
TEXT_CAP = 8000  # chars of stripped text we keep for downstream LLM input
USER_AGENT = "freelance-copilot-research/1 (+local)"

_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style|noscript|svg|iframe)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")
_NEWLINE_RE = re.compile(r"\n\s*\n+")
_TITLE_RE = re.compile(
    r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL
)
_META_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_DESC_RE = re.compile(
    r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


@dataclass(slots=True)
class FetchedPage:
    final_url: str
    title: str | None
    meta_description: str | None
    text: str  # stripped + truncated body


class UrlFetchError(Exception):
    """Raised when we can't get usable text out of a URL."""


def _strip_html(raw: str) -> str:
    cleaned = _SCRIPT_STYLE_RE.sub(" ", raw)
    cleaned = _TAG_RE.sub(" ", cleaned)
    # Decode the handful of HTML entities that commonly survive a regex strip.
    cleaned = (
        cleaned.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
    cleaned = _WS_RE.sub(" ", cleaned)
    cleaned = _NEWLINE_RE.sub("\n\n", cleaned)
    return cleaned.strip()


def _first_match(pattern: re.Pattern[str], raw: str) -> str | None:
    match = pattern.search(raw)
    if match is None:
        return None
    return match.group(1).strip() or None


async def fetch_page(url: str, *, timeout_s: float = DEFAULT_TIMEOUT_S) -> FetchedPage:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.5"}
    try:
        async with httpx.AsyncClient(
            timeout=timeout_s,
            follow_redirects=True,
            max_redirects=5,
            headers=headers,
        ) as client:
            resp = await client.get(url)
    except httpx.HTTPError as exc:
        raise UrlFetchError(f"Network error fetching {url}: {exc}") from exc

    if resp.status_code >= 400:
        raise UrlFetchError(f"HTTP {resp.status_code} for {resp.url}")

    raw = resp.text[:MAX_BYTES]
    title = _first_match(_TITLE_RE, raw)
    description = _first_match(_META_DESC_RE, raw) or _first_match(_OG_DESC_RE, raw)
    text = _strip_html(raw)[:TEXT_CAP]
    if not text and not title and not description:
        raise UrlFetchError(f"No readable content at {url}")
    return FetchedPage(
        final_url=str(resp.url),
        title=title,
        meta_description=description,
        text=text,
    )
