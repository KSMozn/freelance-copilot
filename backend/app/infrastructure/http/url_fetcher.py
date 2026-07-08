"""Fetch a public URL and reduce it to readable plain text.

Defensive defaults: short timeout, redirect cap, custom UA, size cap. SSRF
guard: the target host must resolve to a public IP, and every redirect hop is
re-validated (redirects are followed manually, not by httpx), so a public URL
cannot bounce the fetch to an internal address.

Residual risk: DNS rebinding between the validation lookup and httpx's own
connect lookup is not fully closed (would require pinning the connection to the
validated IP). Acceptable for this surface; the private-IP block stops the
common metadata/internal-service and redirect vectors.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx

_ALLOWED_SCHEMES = frozenset({"http", "https"})

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


def _assert_public_url(url: str) -> None:
    """Reject non-http(s) schemes and any host that resolves to a
    private/loopback/link-local/reserved/multicast address (SSRF guard)."""
    parsed = urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise UrlFetchError(f"Unsupported URL scheme: {parsed.scheme!r}")
    host = parsed.hostname
    if not host:
        raise UrlFetchError("URL has no host")
    try:
        infos = socket.getaddrinfo(host, parsed.port or 80, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UrlFetchError(f"Cannot resolve host {host!r}: {exc}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise UrlFetchError("Refusing to fetch a non-public address")


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
    # Follow redirects manually so every hop is re-validated against the
    # SSRF guard — httpx's own follow_redirects would happily chase a
    # public URL's 302 into an internal host.
    current = url
    try:
        async with httpx.AsyncClient(
            timeout=timeout_s,
            follow_redirects=False,
            headers=headers,
        ) as client:
            resp = None
            for _ in range(6):
                _assert_public_url(current)
                resp = await client.get(current)
                if resp.is_redirect and "location" in resp.headers:
                    current = urljoin(current, resp.headers["location"])
                    continue
                break
            else:
                raise UrlFetchError(f"Too many redirects fetching {url}")
    except httpx.HTTPError as exc:
        raise UrlFetchError(f"Network error fetching {url}: {exc}") from exc

    if resp is None:
        raise UrlFetchError(f"No response fetching {url}")
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
