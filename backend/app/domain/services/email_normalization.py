"""Canonical email normalization.

The database already enforces case-insensitive matching and uniqueness via
CITEXT (`users`, `admin_users`, `email_otp_codes` — migrations 0001/0015/0031),
so lookups can never split one mailbox into two accounts on casing. This
helper canonicalizes what we *store and compare in Python* — lowercase,
trimmed — so in-memory fakes, provider payloads, and log lines agree with the
database's semantics regardless of how the user typed their address.
"""
from __future__ import annotations


def normalize_email(raw: str) -> str:
    return raw.strip().lower()
