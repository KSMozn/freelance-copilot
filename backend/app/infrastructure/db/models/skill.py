from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, TimestampMixin, UUIDPKMixin

SkillKindEnum = SAEnum("technical", "domain", "soft", name="skill_kind", create_type=True)


class Skill(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    kind: Mapped[str] = mapped_column(SkillKindEnum, nullable=False, default="technical")
