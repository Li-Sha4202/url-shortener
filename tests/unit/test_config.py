import pytest

from pydantic import PostgresDsn
from pydantic_settings import SettingsConfigDict

# Импортируем классы конфигурации, которые нужны для тестирования
# Примечание: Мы тестируем сами модели данных, а не глобальный экземпляр settings()
# так как instantiation экземпляра зависит от окружения (.env), что сложнее мокировать.

from src.core.config import (
    RunConfig,
    LinkSchemaConfig,
    UserSchemaConfig,
    DataBaseSettings,
    JWTSettings,
    Settings,
)


class TestRunConfig:
    """Тест для конфигурации запуска сервера"""

    def test_default_values(self):
        """Проверка значений по умолчанию"""
        config = RunConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.reload is True


class TestLinkSchemaConfig:
    """Тесты для конфигурации схемы ссылок"""

    def test_default_values(self):
        """Проверка значений по умолчанию"""
        config = LinkSchemaConfig()
        assert config.shortcode_min_length == 5
        assert config.shortcode_max_length == 20
        assert config.expire_in_days_min_length == -1
        assert config.expire_in_days_max_length == 365


class TestUserSchemaConfig:
    """Тесты для конфигурации схемы пользователей"""

    def test_default_values(self):
        """Проверка значений по умолчанию"""
        config = UserSchemaConfig()
        assert config.username_min_length == 5
        assert config.username_max_length == 32
        assert config.password_min_length == 8


class TestDataBaseSettings:
    """Тесты для конфигурации БД"""

    def test_default_values_except_url(self):
        """
        Проверка значений по умолчанию.
        URL не имеет значения по умолчанию, поэтому его нельзя проверить здесь без мокирования.
        """
        config = DataBaseSettings(url="postgresql://user:pass@localhost/dbname")  # type: ignore
        assert config.echo is False
        assert config.pool_pre_ping is True
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.autoflush is False
        assert config.expire_on_commit is False


class TestJWTSettings:
    """Тесты для конфигурации JWT"""

    def test_required_secret_key(self):
        """jwt_secret_key является обязательным полем"""
        with pytest.raises(Exception):  # Pydantic raises ValidationError
            JWTSettings()  # type: ignore

    def test_default_values_with_secret(self):
        """Проверка значений по умолначию при наличии секрета"""
        config = JWTSettings(SECRET_KEY="test_secret_key")
        assert config.ALGORITHM == "HS256"
        assert config.ACCESS_TOKEN_EXPIRE_MINUTES == 30


class TestSettings:
    """Тесты для основного класса Settings"""

    def test_settings_class_structure(self):
        """
        Проверяем, что класс Settings имеет ожидаемые атрибуты
        Мы не создаем полный экземпляр здесь, так как он требует env vars.
        Вместо этого проверяем наличие полей через модель.
        """
        # Проверяем, что model_fields существует и содержит нужные ключи
        assert "run" in Settings.model_fields
        assert "db" in Settings.model_fields
        assert "ls" in Settings.model_fields
        assert "usc" in Settings.model_fields
        assert "jwt" in Settings.model_fields

    def test_env_config(self):
        """Проверка настроек парсинга окружения"""
        # Проверяем, что модель имеет правильный конфигурационный класс
        config_dict = Settings.model_config
        assert config_dict.get("env_file") == ".env"
        assert config_dict.get("case_sensitive") is False
        assert config_dict.get("env_nested_delimiter") == "__"
        assert config_dict.get("env_prefix") == "APP_CONFIG__"
