from pydantic import BaseModel
from pydantic_settings import BaseSettings


class RunConfig(BaseModel):
    """Настройки запуска приложения."""

    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True


class Settings(BaseSettings):
    """Класс для последующего считывания переменных окружения."""

    run = RunConfig()


settings = Settings()
