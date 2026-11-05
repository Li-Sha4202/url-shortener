import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from src.features.users.schema import (
    UserCreateSchema,
    UserResponseSchema,
    UserUpdateSchema,
    ChangePasswordSchema,
    AccountDelete,
)
from src.features.links.schema import LinkCreate, LinkResponse, LinkUpdate
from src.core.config import settings


class TestUserSchemas:
    """Тесты для схем User и Link"""

    # --- Test UserCreateSchema ---
    def test_user_create_valid(self):
        """Проверка валидного создания пользователя"""
        user_data = {
            "name": "valid_user",
            "email": "test@example.com",
            "password": "strongpassword123",
        }
        user = UserCreateSchema(**user_data)
        assert user.name == "valid_user"
        assert user.email == "test@example.com"
        # Пароль в ответе может быть скрыт или приведён к типу str, проверяем наличие
        assert user.password is not None

    def test_user_create_short_name(self):
        """Проверка, что имя пользователя меньше минимальной длины вызывает ошибку"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreateSchema(
                name="ab",
                email="test@example.com",
                password="strongpassword123",
            )
            assert "name" in str(exc_info.value)

    def test_user_create_short_password(self):
        """Проверка, что пароль короче минимальной длины вызывает ошибку"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreateSchema(
                name="valid_user",
                email="user@example.com",
                password="123",
            )
        assert "password" in str(exc_info.value)

    def test_user_create_invalid_email(self):
        """Проверка невалидного email"""
        with pytest.raises(ValidationError):
            UserCreateSchema(
                name="valid_user",
                email="not-an-email",
                password="strongpassword123",
            )

    # --- Test UserUpdate ---
    def test_user_update_partial(self):
        """Обновление только поля name"""
        update_data = {"name": "new_name"}
        user_update = UserUpdateSchema(**update_data)
        assert user_update.name == "new_name"
        assert user_update.email is None

    def test_user_update_forbid_extra(self):
        """Проверка, что extra поля запрещены (extra="forbid")"""

        with pytest.raises(ValidationError):
            UserUpdateSchema(  # type: ignore
                name="test",
                field_that_does_not_exist="bad_value",  # type: ignore
            )

    # --- Test ChangePasswordSchema ---

    def test_change_password_valid(self):
        """Валидное обновление пароля"""
        password_data = {
            "current_password": "oldpassword123",
            "new_password": "newstrongpass123",
        }
        schema = ChangePasswordSchema(**password_data)
        assert schema.current_password == "oldpassword123"
        assert schema.new_password == "newstrongpass123"

    def test_change_password_short_new_password(self):
        """Новый пароль короче минимальной длины вызывает ошибку"""
        with pytest.raises(ValidationError):
            ChangePasswordSchema(
                current_password="oldpassword123",
                new_password="short",
            )

    def test_change_password_missing_current_password(self):
        """Отсутствие current_password вызывает ошибку"""
        with pytest.raises(ValidationError):
            ChangePasswordSchema(
                new_password="newstrongpass123",
            )


class TestLinkSchemas:
    """Тесты для схем ссылок"""

    # --- Test LinkCreate ---
    def test_link_create_custom_code_valid(self):
        """Создание ссылки с валидным кастомным кодом"""
        link_data = {
            "original_url": "https://example.com",
            "short_code": "my-link-1",
        }
        link = LinkCreate(**link_data)  # type: ignore
        assert link.short_code == "my-link-1"

    def test_link_create_custom_code_invalid(self):
        """Создание ссылки с невалидным кодом (содержит пробел или спецсимволы)"""
        with pytest.raises(ValidationError):
            LinkCreate(
                original_url="https://www.google.com",  # type: ignore
                short_code="bad code",
            )

    def test_link_create_expires_at_bounds(self):
        """Проверка границ expires_at"""
        # Минимальное значение
        min_days = settings.ls.expire_in_days_min_length
        # Максимальное значение
        max_days = settings.ls.expire_in_days_max_length

        # Валидный минимум
        link_min = LinkCreate(
            original_url="https://www.google.com",  # type: ignore
            expires_at_days=min_days,
        )
        assert link_min.expires_at_days == min_days

        # Валидный максимум
        link_max = LinkCreate(
            original_url="https://www.google.com",  # type: ignore
            expires_at_days=max_days,
        )
        assert link_max.expires_at_days == max_days

        # Слишком мало
        with pytest.raises(ValidationError):
            LinkCreate(  # type: ignore
                original_url="https://www.google.com", expires_at_days=min_days - 1
            )

        # Слишком много
        with pytest.raises(ValidationError):
            LinkCreate(  # type: ignore
                original_url="https://www.google.com", expires_at_days=max_days + 1
            )

    # --- Test LinkResponse ---
    def test_link_response_short_url(self):
        """Проверка вычисленного поля short_url"""
        # Mock settings, так как в тестовой среде хост/порт могут не совпадать или отсутствовать
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(settings.run, "host", "0.0.0.0")
            mp.setattr(settings.run, "port", "8000")

            link_data = {
                "short_code": "abc123",
                "original_url": "https://example.com",
                "created_at": datetime.now(timezone.utc),
            }
            response = LinkResponse(**link_data)

            expected_url = "http://localhost:8000/abc123"
            assert response.short_url == expected_url

    # --- Test LinkUpdate ---
    def test_link_update_valid(self):
        """Валидное обновление ссылки"""
        update_data = {"original_url": "https://new_url.com"}
        link_update = LinkUpdate(**update_data)  # type: ignore
        assert link_update.original_url is not None

    def test_link_update_forbid_extra(self):
        """Проверка запрета лишних полей"""
        with pytest.raises(ValidationError):
            LinkUpdate(
                original_url="https://new.com",
                bad_field="value",  # type: ignore
            )
