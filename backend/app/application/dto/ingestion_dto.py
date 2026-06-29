from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import AnyUrl, BaseModel, ConfigDict, Field

ParseStatusLiteral = Literal["pending", "parsing", "parsed", "failed"]
ContentTypeLiteral = Literal["blog_post", "talk", "paper", "open_source"]


# ---- CV uploads ----------------------------------------------------------


class CvUploadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    persona_id: UUID | None
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    parse_status: ParseStatusLiteral
    parse_error: str | None = None
    extracted_structure: dict[str, Any] = Field(default_factory=dict)
    extracted_skills: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PastedCvRequest(BaseModel):
    """Alternative to multipart upload: paste raw CV text directly."""

    title: str = Field(default="Pasted CV", max_length=255)
    text: str = Field(min_length=1, max_length=200_000)
    persona_id: UUID | None = None


# ---- LinkedIn snapshots --------------------------------------------------


class LinkedInSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    parse_status: ParseStatusLiteral
    parse_error: str | None = None
    extracted_structure: dict[str, Any] = Field(default_factory=dict)
    parsed_at: datetime | None = None
    created_at: datetime | None = None


# ---- Certificates --------------------------------------------------------


class CertificateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    issuer: str
    issued_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = None
    credential_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CertificateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    issuer: str = Field(min_length=1, max_length=255)
    issued_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = Field(default=None, max_length=255)
    credential_url: AnyUrl | None = None


class CertificateUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    issuer: str | None = Field(default=None, max_length=255)
    issued_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = Field(default=None, max_length=255)
    credential_url: AnyUrl | None = None


# ---- Content items -------------------------------------------------------


class ContentItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    type: ContentTypeLiteral
    title: str
    url: str | None = None
    published_date: date | None = None
    summary: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ContentItemCreate(BaseModel):
    type: ContentTypeLiteral = "blog_post"
    title: str = Field(min_length=1, max_length=512)
    url: AnyUrl | None = None
    published_date: date | None = None
    summary: str | None = Field(default=None, max_length=2000)
    raw_text: str | None = Field(default=None, max_length=200_000)


class ContentItemUpdate(BaseModel):
    type: ContentTypeLiteral | None = None
    title: str | None = Field(default=None, max_length=512)
    url: AnyUrl | None = None
    published_date: date | None = None
    summary: str | None = Field(default=None, max_length=2000)
    raw_text: str | None = Field(default=None, max_length=200_000)
