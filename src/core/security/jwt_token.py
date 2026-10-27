from datetime import datetime, timezone, timedelta
from jose import jwt

from src.core.config import settings


def create_access_token(user_id: int, expire_delta: timedelta | None = None) -> str:
    """Создание Access-JWT токена"""
    now = datetime.now(timezone.utc)
    expire = now + (
        expire_delta or timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    data = {
        "sub": str(user_id),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access",
    }
    encode = jwt.encode(data, settings.jwt.SECRET_KEY, settings.jwt.ALGORITHM)
    return encode


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt.SECRET_KEY, settings.jwt.ALGORITHM)
