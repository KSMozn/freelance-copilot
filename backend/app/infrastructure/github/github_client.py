"""Thin async client over the GitHub REST API.

Authenticated when GITHUB_TOKEN is set in settings; otherwise falls back to
unauthenticated calls (60 req/hr/IP). Only the read endpoints the scanner
needs are exposed.
"""
from __future__ import annotations

import base64
import re
from dataclasses import dataclass

import httpx

GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<name>[^/#?]+?)(?:\.git)?/?(?:[#?].*)?$",
    re.IGNORECASE,
)


def parse_github_url(url: str) -> tuple[str, str]:
    """Parse a GitHub repo URL into (owner, name). Raises ValueError on miss."""
    match = GITHUB_URL_RE.match(url.strip())
    if not match:
        raise ValueError(f"Not a recognizable github.com repo URL: {url!r}")
    return match.group("owner"), match.group("name")


@dataclass(slots=True)
class GithubFile:
    path: str
    content: str  # decoded UTF-8 text, "" if binary or unreadable


@dataclass(slots=True)
class GithubRepoMetadata:
    owner: str
    name: str
    description: str | None
    default_branch: str
    languages: dict[str, int]


class GithubError(Exception):
    """Raised when GitHub returns a non-recoverable error (404, 401, 5xx)."""


class GithubClient:
    def __init__(
        self,
        *,
        token: str | None,
        base_url: str = "https://api.github.com",
        timeout_s: float = 20.0,
    ) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "freelance-copilot-scanner/1",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=timeout_s,
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> GithubClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def get_repo(self, owner: str, name: str) -> GithubRepoMetadata:
        repo = await self._get_json(f"/repos/{owner}/{name}")
        languages = await self._get_json(f"/repos/{owner}/{name}/languages")
        return GithubRepoMetadata(
            owner=repo["owner"]["login"],
            name=repo["name"],
            description=repo.get("description"),
            default_branch=repo.get("default_branch") or "main",
            languages={k: int(v) for k, v in (languages or {}).items()},
        )

    async def get_file(self, owner: str, name: str, path: str, *, ref: str | None = None) -> GithubFile | None:
        """Fetch a single file's text content. Returns None on 404; raises on
        other errors. Binary files come back as empty string.
        """
        params = {"ref": ref} if ref else None
        try:
            payload = await self._get_json(
                f"/repos/{owner}/{name}/contents/{path}", params=params
            )
        except GithubError as exc:
            if "404" in str(exc):
                return None
            raise
        if isinstance(payload, list):
            # `path` pointed at a directory — caller should use list_dir
            return None
        encoding = payload.get("encoding")
        raw = payload.get("content") or ""
        if encoding == "base64":
            try:
                text = base64.b64decode(raw).decode("utf-8", errors="replace")
            except Exception:
                text = ""
        else:
            text = raw if isinstance(raw, str) else ""
        return GithubFile(path=path, content=text)

    async def get_tree(
        self, owner: str, name: str, *, sha: str, recursive: bool = True
    ) -> list[dict]:
        """Fetch the repo's file tree. Returns the raw `tree` array — each entry
        has `path`, `type` ('blob' | 'tree'), and `sha`. Empty list on 404.
        """
        params = {"recursive": "1"} if recursive else None
        try:
            payload = await self._get_json(
                f"/repos/{owner}/{name}/git/trees/{sha}", params=params
            )
        except GithubError as exc:
            if "404" in str(exc):
                return []
            raise
        entries = payload.get("tree") if isinstance(payload, dict) else None
        if not isinstance(entries, list):
            return []
        return entries

    async def list_dir(self, owner: str, name: str, path: str, *, ref: str | None = None) -> list[str]:
        """Return entry names in a directory. Empty list on 404."""
        params = {"ref": ref} if ref else None
        try:
            payload = await self._get_json(
                f"/repos/{owner}/{name}/contents/{path}", params=params
            )
        except GithubError as exc:
            if "404" in str(exc):
                return []
            raise
        if not isinstance(payload, list):
            return []
        return [entry["name"] for entry in payload if isinstance(entry, dict) and "name" in entry]

    async def _get_json(self, path: str, *, params: dict[str, str] | None = None):
        resp = await self._client.get(path, params=params)
        if resp.status_code == 404:
            raise GithubError(f"GitHub 404 for {path}")
        if resp.status_code == 403:
            raise GithubError(
                f"GitHub 403 for {path} — rate-limited or private repo without token"
            )
        if resp.status_code >= 400:
            raise GithubError(f"GitHub {resp.status_code} for {path}: {resp.text[:200]}")
        return resp.json()
