from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class AdminUser:
    id: UUID
    email: str
    password_hash: str
    full_name: str | None
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
