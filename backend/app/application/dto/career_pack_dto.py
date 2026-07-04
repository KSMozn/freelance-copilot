"""DTOs for the post-CV Career Starter Pack cards (LinkedIn + GitHub).

All content flows through here in strict Pydantic shapes so the LLM
provider can't leak arbitrary fields into stored state. Every list of
strings is capped at a reasonable size — the goal is student-friendly
brevity, not exhaustive dumps.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

CareerStatus = Literal["missing", "started", "needs_improvement", "completed"]


# --- LinkedIn generate --------------------------------------------------


class LinkedInProjectSuggestion(BaseModel):
    """One LinkedIn Featured Project entry, ready to paste."""

    name: str
    description: str


class LinkedInGenerated(BaseModel):
    """Full LinkedIn starter kit generated from the student's CV."""

    headline: str = Field(max_length=220)
    about: str
    education_entry: str
    project_entries: list[LinkedInProjectSuggestion] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list, max_length=30)
    checklist: list[str] = Field(default_factory=list, max_length=15)


# --- LinkedIn review ----------------------------------------------------


class LinkedInReview(BaseModel):
    summary: str
    current_headline_review: str | None = None
    suggested_headline: str | None = None
    current_about_review: str | None = None
    suggested_about: str | None = None
    missing_sections: list[str] = Field(default_factory=list, max_length=10)
    skills_to_add: list[str] = Field(default_factory=list, max_length=15)
    projects_to_improve: list[str] = Field(default_factory=list, max_length=10)
    checklist: list[str] = Field(default_factory=list, max_length=15)


# --- GitHub generate ----------------------------------------------------


class GitHubProjectReadme(BaseModel):
    """One project README, keyed by the CV project title."""

    project_title: str
    filename: str = "README.md"
    body: str


class GitHubGenerated(BaseModel):
    username_suggestions: list[str] = Field(default_factory=list, max_length=6)
    bio: str = Field(max_length=160)
    profile_readme: str
    project_readmes: list[GitHubProjectReadme] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list, max_length=15)


# --- GitHub review ------------------------------------------------------


class GitHubReview(BaseModel):
    profile_summary: str
    has_profile_readme: bool | None = None
    suggested_bio: str | None = None
    suggested_profile_readme: str | None = None
    project_readme_suggestions: list[GitHubProjectReadme] = Field(default_factory=list)
    repo_checklist: list[str] = Field(default_factory=list, max_length=15)
    cv_projects_to_add: list[str] = Field(default_factory=list, max_length=10)


class GitHubReviewRequest(BaseModel):
    # Accept either a raw username or a github.com URL; the service
    # normalizes to a username before calling the public API.
    identifier: str = Field(
        min_length=1,
        max_length=120,
        description="GitHub username OR a github.com profile URL.",
    )


# --- Read model ---------------------------------------------------------


class CareerPackRead(BaseModel):
    """Aggregate state shown on the Career Starter Pack page."""

    linkedin_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    linkedin_status: CareerStatus
    github_status: CareerStatus
    # Last generated / reviewed payloads, so returning to the card
    # shows the previous result without re-spending an AI call.
    linkedin_generated: LinkedInGenerated | None = None
    linkedin_recommendations: LinkedInReview | None = None
    github_generated: GitHubGenerated | None = None
    github_recommendations: GitHubReview | None = None
    github_username: str | None = None


class ClearRequest(BaseModel):
    """Clear either the generated starter content or the review recommendations
    for one side of the card. The saved URL and status stay put — only the
    AI-produced payload disappears.
    """

    side: Literal["linkedin", "github"]
    kind: Literal["generated", "recommendations"]
