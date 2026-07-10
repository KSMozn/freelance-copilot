from pydantic import BaseModel, ConfigDict, Field


class DevEmailRead(BaseModel):
    """One captured email from the mock provider's dev outbox."""

    model_config = ConfigDict(extra="ignore")

    ts: str
    to: str
    subject: str
    text_body: str
    tags: dict[str, str] = Field(default_factory=dict)


class DevMailboxResponse(BaseModel):
    emails: list[DevEmailRead]
