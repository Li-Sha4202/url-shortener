from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime

from db.base import Base

if TYPE_CHECKING:
    from features.links.model import Link


class User(Base):
    """SQL - Модель пользователя"""

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32))
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
    )

    links: Mapped[list["Link"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )
