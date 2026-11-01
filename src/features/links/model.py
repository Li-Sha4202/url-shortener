from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.features.users.model import User


class Link(Base):
    """SQL - Модель ссылки"""

    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_url: Mapped[str] = mapped_column()
    short_code: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    first_click: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_click: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    clicks_count: Mapped[int] = mapped_column(default=0)

    clicks_by_day: Mapped[dict[str, int] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    user: Mapped["User | None"] = relationship(
        back_populates="links",
        lazy="selectin",
    )
