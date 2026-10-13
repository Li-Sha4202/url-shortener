from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from features.users.model import User


class Link(Base):
    """SQL - Модель ссылки"""

    id: Mapped[int] = mapped_column(primary_key=True)
    original_url: Mapped[str] = mapped_column()
    short_code: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
    )

    first_click: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_click: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    clicks_count: Mapped[datetime] = mapped_column(default=0)

    clicks_by_day: Mapped[dict[str, int]] = mapped_column(
        JSON,
        nullable=True,
        default={},
    )

    user: Mapped["User"] = relationship(
        back_populates="links",
        lazy="selectin",
    )
