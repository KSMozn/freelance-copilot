from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

ParseStatus = Literal["pending", "parsing", "parsed", "failed"]
ContentType = Literal["blog_post", "talk", "paper", "open_source"]


@dataclass(slots=True)
class UploadedFileEntry:
    id: UUID
    user_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    sha256: str
    created_at: datetime | None = None


@dataclass(slots=True)
class CvUploadEntry:
    id: UUID
    user_id: UUID
    persona_id: UUID | None
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str | None
    sha256: str
    extracted_text: str | None
    parse_status: ParseStatus
    parse_error: str | None
    extracted_structure: dict[str, Any] = field(default_factory=dict)
    extracted_skills: list[Any] = field(default_factory=list)
    resume_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class LinkedInSnapshotEntry:
    id: UUID
    user_id: UUID
    file_id: UUID | None
    extracted_text: str | None
    extracted_structure: dict[str, Any] = field(default_factory=dict)
    parse_status: ParseStatus = "pending"
    parse_error: str | None = None
    parsed_at: datetime | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class CertificateEntry:
    id: UUID
    user_id: UUID
    name: str
    issuer: str
    issued_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = None
    credential_url: str | None = None
    file_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ContentItemEntry:
    id: UUID
    user_id: UUID
    type: ContentType
    title: str
    url: str | None = None
    published_date: date | None = None
    summary: str | None = None
    raw_text: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
