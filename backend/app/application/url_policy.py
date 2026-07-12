from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit

_LEGACY_NUMERIC_PART = re.compile(r"(?:0[xX][0-9A-Fa-f]+|[0-9]+)\Z")


def normalize_external_http_url(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    if "\\" in stripped or any(ord(char) < 32 or ord(char) == 127 for char in stripped):
        raise ValueError("URL must use http:// or https://")
    try:
        parsed = urlsplit(stripped)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("URL must use http:// or https://") from exc
    scheme = parsed.scheme.lower()
    host = parsed.hostname
    if (
        scheme not in {"http", "https"}
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or "%" in host
    ):
        raise ValueError("URL must use http:// or https://")
    normalized_host = host.rstrip(".")

    try:
        ip = ipaddress.ip_address(normalized_host)
        canonical_host = ip.compressed
        host_part = f"[{canonical_host}]" if ip.version == 6 else canonical_host
    except ValueError:
        if all(_LEGACY_NUMERIC_PART.fullmatch(part) for part in normalized_host.split(".")):
            raise ValueError("URL has an ambiguous numeric host") from None
        try:
            canonical_host = normalized_host.encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise ValueError("URL has an invalid host") from exc
        host_part = canonical_host
    if not canonical_host:
        raise ValueError("URL has an invalid host")

    netloc = f"{host_part}:{port}" if port is not None else host_part
    return urlunsplit((scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def safe_external_http_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        return normalize_external_http_url(value)
    except ValueError:
        return None
