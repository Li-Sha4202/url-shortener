from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunConfig(BaseModel):
    """Настройки запуска приложения."""

    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    public_url: str = "http://localhost"


class DataBaseSettings(BaseModel):
    """Конфигурация Базы Данных"""

    url: PostgresDsn
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_pre_ping: bool = True
    pool_recycle: int = 3600
    expire_on_commit: bool = False
    autoflush: bool = False


class UserSchemaConfig(BaseModel):
    """Конфигурация Pydantic-схемы пользователя"""

    username_min_length: int = 5
    username_max_length: int = 32

    password_min_length: int = 8


class LinkSchemaConfig(BaseModel):
    """Конфигурация Pydantic-схемы ссылки"""

    expire_in_days_min_length: int = 1
    expire_in_days_max_length: int = 365

    shortcode_min_length: int = 8
    shortcode_max_length: int = 20


class JWTSettings(BaseModel):
    """Настройки создания JWT-токена"""

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


class Settings(BaseSettings):
    """Класс для последующего считывания переменных окружения."""

    model_config = SettingsConfigDict(
        env_file=(".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )

    run: RunConfig = RunConfig()
    db: DataBaseSettings
    usc: UserSchemaConfig = UserSchemaConfig()
    ls: LinkSchemaConfig = LinkSchemaConfig()
    jwt: JWTSettings


settings = Settings()  # type: ignore
