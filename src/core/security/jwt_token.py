from datetime import datetime, timezone, timedelta
from jose import jwt

from src.core.config import settings


def create_access_token(user_id: int, expire_delta: timedelta | None = None) -> str:
    """Создание Access-JWT токена"""
    expire = datetime.now(timezone.utc) + (
        expire_delta or timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    data = {"sub": user_id, "expire_at": expire}
    encode = jwt.encode(data, settings.jwt.SECRET_KEY, settings.jwt.ALGORITHM)
    return encode


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt.SECRET_KEY, settings.jwt.ALGORITHM)
