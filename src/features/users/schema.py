from datetime import datetime

from typing import Optional

from pydantic import BaseModel, Field, EmailStr

from core.config import settings


class UserCreate(BaseModel):
    """Схема для создания пользователя"""

    username: str = Field(
        ...,
        min_length=settings.usc.username_min_length,
        max_length=settings.usc.username_max_length,
        description="Имя пользователя",
    )

    email: EmailStr = Field(
        ...,
        description="Почта пользователя",
    )

    password: str = Field(
        ...,
        min_length=settings.usc.password_min_length,
        description="Пароль пользователя (Минимум 8 символов)",
    )


class UserResponse(BaseModel):
    """Схема ответа на запрос о пользователе"""

    username: str = Field(
        ...,
        description="Имя пользователя",
    )

    email: str = Field(
        ...,
        description="Электронная почта пользователя",
    )

    created_at: datetime = Field(
        ...,
        description="Дата регистрации",
    )

    is_admin: bool = Field(
        ...,
        description="Является ли администратором",
    )
