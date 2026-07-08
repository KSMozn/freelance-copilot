"""Unit tests for refresh-token rotation + reuse detection."""
from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.application.services.refresh_token_manager import RefreshTokenManager
from app.core.security import decode_token
from app.domain.entities.refresh_token import RefreshTokenRecord
from app.domain.exceptions import InvalidCredentialsError


class FakeRefreshTokenRepo:
    """In-memory mirror of SQLAlchemyRefreshTokenRepository semantics."""

    def __init__(self) -> None:
        self.rows: dict[UUID, RefreshTokenRecord] = {}

    async def create(
        self, *, jti, family_id, principal_type, subject_id, expires_at
    ) -> None:
        now = datetime.now(UTC)
        self.rows[jti] = RefreshTokenRecord(
            id=jti,
            family_id=family_id,
            principal_type=principal_type,
            subject_id=subject_id,
            expires_at=expires_at,
            revoked_at=None,
            revoked_reason=None,
            created_at=now,
        )

    async def get(self, jti):
        return self.rows.get(jti)

    async def revoke(self, jti, *, reason, at) -> None:
        row = self.rows.get(jti)
        if row is not None and row.revoked_at is None:
            self.rows[jti] = dataclasses.replace(
                row, revoked_at=at, revoked_reason=reason
            )

    async def revoke_family(self, family_id, *, reason, at) -> None:
        for jti, row in list(self.rows.items()):
            if row.family_id == family_id and row.revoked_at is None:
                self.rows[jti] = dataclasses.replace(
                    row, revoked_at=at, revoked_reason=reason
                )


def _payload(refresh_token: str) -> dict:
    return decode_token(refresh_token, "refresh")


async def test_issue_embeds_jti_and_family() -> None:
    repo = FakeRefreshTokenRepo()
    mgr = RefreshTokenManager(repo)
    uid = uuid4()
    _, refresh = await mgr.issue(uid, "user")
    data = _payload(refresh)
    assert data["sub"] == str(uid)
    assert data["pt"] == "user"
    assert "jti" in data and "fid" in data
    assert len(repo.rows) == 1


async def test_rotate_revokes_old_and_issues_successor() -> None:
    repo = FakeRefreshTokenRepo()
    mgr = RefreshTokenManager(repo)
    uid = uuid4()
    _, refresh = await mgr.issue(uid, "user")
    old = _payload(refresh)
    _, new_refresh = await mgr.rotate(old, "user", uid)
    new = _payload(new_refresh)

    # Old token now revoked as "rotated"; successor lives in same family.
    old_row = repo.rows[UUID(old["jti"])]
    assert old_row.revoked_reason == "rotated"
    assert new["fid"] == old["fid"]
    assert new["jti"] != old["jti"]
    new_row = repo.rows[UUID(new["jti"])]
    assert new_row.revoked_at is None


async def test_reuse_after_grace_revokes_whole_family() -> None:
    repo = FakeRefreshTokenRepo()
    mgr = RefreshTokenManager(repo)
    uid = uuid4()
    _, refresh = await mgr.issue(uid, "user")
    old = _payload(refresh)
    _, new_refresh = await mgr.rotate(old, "user", uid)  # rotate once
    new = _payload(new_refresh)

    # Backdate the old token's revocation beyond the grace window.
    old_jti = UUID(old["jti"])
    repo.rows[old_jti] = dataclasses.replace(
        repo.rows[old_jti], revoked_at=datetime.now(UTC) - timedelta(minutes=5)
    )

    # Replaying the already-rotated token is theft → family nuked.
    with pytest.raises(InvalidCredentialsError):
        await mgr.rotate(old, "user", uid)
    assert repo.rows[UUID(new["jti"])].revoked_reason == "reuse_detected"


async def test_reuse_within_grace_rejects_but_keeps_family_alive() -> None:
    repo = FakeRefreshTokenRepo()
    mgr = RefreshTokenManager(repo)
    uid = uuid4()
    _, refresh = await mgr.issue(uid, "user")
    old = _payload(refresh)
    _, new_refresh = await mgr.rotate(old, "user", uid)
    new = _payload(new_refresh)

    # Immediate replay (double-submit) — rejected, but successor stays valid.
    with pytest.raises(InvalidCredentialsError):
        await mgr.rotate(old, "user", uid)
    assert repo.rows[UUID(new["jti"])].revoked_at is None


async def test_logout_revokes_family() -> None:
    repo = FakeRefreshTokenRepo()
    mgr = RefreshTokenManager(repo)
    uid = uuid4()
    _, refresh = await mgr.issue(uid, "user")
    data = _payload(refresh)
    await mgr.revoke_session(data)
    assert repo.rows[UUID(data["jti"])].revoked_reason == "logout"
    # A revoked token can no longer be rotated.
    with pytest.raises(InvalidCredentialsError):
        await mgr.rotate(data, "user", uid)


async def test_unknown_jti_rejected() -> None:
    repo = FakeRefreshTokenRepo()
    mgr = RefreshTokenManager(repo)
    uid = uuid4()
    forged = {"sub": str(uid), "pt": "user", "jti": str(uuid4()), "fid": str(uuid4())}
    with pytest.raises(InvalidCredentialsError):
        await mgr.rotate(forged, "user", uid)


async def test_legacy_token_without_jti_bootstraps() -> None:
    repo = FakeRefreshTokenRepo()
    mgr = RefreshTokenManager(repo)
    uid = uuid4()
    legacy = {"sub": str(uid), "pt": "user"}  # pre-feature token: no jti/fid
    _, refresh = await mgr.rotate(legacy, "user", uid)
    data = _payload(refresh)
    assert "jti" in data
    assert len(repo.rows) == 1  # a fresh tracked family was created


async def test_expired_row_rejected() -> None:
    repo = FakeRefreshTokenRepo()
    mgr = RefreshTokenManager(repo)
    uid = uuid4()
    _, refresh = await mgr.issue(uid, "user")
    data = _payload(refresh)
    jti = UUID(data["jti"])
    repo.rows[jti] = dataclasses.replace(
        repo.rows[jti], expires_at=datetime.now(UTC) - timedelta(seconds=1)
    )
    with pytest.raises(InvalidCredentialsError):
        await mgr.rotate(data, "user", uid)
