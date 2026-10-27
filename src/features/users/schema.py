from datetime import datetime

from typing import Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict

from src.core.config import settings


class UserCreateSchema(BaseModel):
    """Схема для создания пользователя"""

    name: str = Field(
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


class UserResponseSchema(BaseModel):
    """Схема ответа на запрос о пользователе"""

    name: str = Field(
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

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserUpdateSchema(BaseModel):
    """Схема обновления аккаунта пользователя"""

    name: str | None = Field(
        None,
        min_length=settings.usc.username_min_length,
        max_length=settings.usc.username_max_length,
        description="Имя пользователя",
    )

    email: EmailStr | None = Field(
        None,
        description="Почта пользователя",
    )
    current_password: str | None = None  # нужен, если меняется email


class ChangePasswordSchema(BaseModel):
    """Схема обновления пароля"""

    current_password: str
    new_password: str = Field(
        ...,
        min_length=settings.usc.password_min_length,
        description="Новый пароль пользователя (Минимум 8 символов)",
    )


class AccountDelete(BaseModel):
    """Схема удаления аккаунта"""

    current_password: str
