from datetime import datetime
from typing import Optional, Dict, Annotated

from pydantic import (
    Field,
    BaseModel,
    HttpUrl,
    computed_field,
    ConfigDict,
)
from pydantic.types import StringConstraints

from src.core.config import settings

# Алиас для валидации кастомной ссылки
ShortCode = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=settings.ls.shortcode_min_length,
        max_length=settings.ls.shortcode_max_length,
        pattern=r"^[a-zA-Z0-9_-]+$",
    ),
]


class LinkBase(BaseModel):
    """Базовая модель, не используется сама по себе"""

    original_url: HttpUrl = Field(
        ...,
        description="Оригинальный URL (Должен начинаться с http:// или https://)",
    )


class LinkCreate(LinkBase):
    """Модель для создания ссылки"""

    short_code: ShortCode | None = None

    expires_at_days: Optional[int] = Field(  # Измеряется в днях
        default=None,
        ge=settings.ls.expire_in_days_min_length,  # Минимальный срок жизни ссылки
        le=settings.ls.expire_in_days_max_length,  # Максимальный срок жизни ссылки
        description=("Время истечения ссылки (Опционально)" "По умолчанию не истекает"),
    )

    model_config = ConfigDict(extra="forbid")


class LinkResponse(BaseModel):
    """Модель для ответа серверу, когда ссылка уже создана"""

    short_code: str
    original_url: str
    created_at: datetime
    expires_at: datetime | None = None

    @computed_field
    @property
    def short_url(self) -> str:
        """Полный URL с короткой ссылкой"""
        return f"{settings.run.public_url}/{self.short_code}"


class LinkStats(BaseModel):
    """Статистика по короткой ссылке"""

    short_code: str
    clicks_count: int
    first_click: datetime | None = None
    last_click: datetime | None = None
    clicks_by_day: Dict[str, int] = Field(
        default_factory=dict,
        description="Количество переходов за день",
    )

    model_config = ConfigDict(from_attributes=True)


class LinkStatsAll(BaseModel):
    """Общая статистика по всем ссылкам"""

    total_clicks: int
    total_links: int
    active_links: int
    expired_links: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class LinkStatsTop(BaseModel):
    """Топ популярных ссылок"""

    short_code: str
    original_url: str
    clicks_count: int
    created_at: datetime

    @computed_field
    @property
    def short_url(self) -> str:
        """Полный URL с короткой ссылкой"""
        return f"{settings.run.public_url}/{self.short_code}"

    model_config = ConfigDict(
        from_attributes=True,
    )


class LinksMe(BaseModel):
    """Схема данных о ссылке, только по user_id"""

    user_id: int
    short_code: str
    original_url: str
    created_at: datetime
    expires_at_days: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )

    @computed_field
    @property
    def short_url(self) -> str:
        """Полный URL с короткой ссылкой"""
        return f"{settings.run.public_url}/{self.short_code}"


class LinkUpdate(BaseModel):
    """Схема для обновления ссылки"""

    original_url: HttpUrl | None = None

    expires_at_days: Optional[int] = Field(
        default=None,
        ge=settings.ls.expire_in_days_min_length,
        le=settings.ls.expire_in_days_max_length,
        description=(
            "Срок ссылки в днях. "
            "-1 = убрать срок (т.е. бессрочная ссылка)"
            "1-365 = установить срок."
            "Не передавать - не менять."
        ),
    )

    model_config = ConfigDict(extra="forbid")
