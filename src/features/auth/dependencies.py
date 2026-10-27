from datetime import datetime, timezone

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from jose.exceptions import JWTError

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import get_session

from src.core.security.jwt_token import decode_access_token

from src.core.exceptions import err_401_not_validate_credentials

from src.features.users.repository import UserRepository
from src.features.users.model import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Получение текущего авторизованного юзера по его jwt-токену"""

    try:
        payload = decode_access_token(token=token)
    except (JWTError, ValueError):
        raise err_401_not_validate_credentials()

    user_id_str: str | None = payload.get("sub")
    iat = payload.get("iat")
    token_type = payload.get("type")

    if user_id_str is None or iat is None or token_type != "access":
        raise err_401_not_validate_credentials()

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise err_401_not_validate_credentials()

    repo = UserRepository(session)
    user = await repo.get_by_id(id=user_id)
    if user is None:
        raise err_401_not_validate_credentials()

    token_issued_at = datetime.fromtimestamp(iat, tz=timezone.utc)
    if token_issued_at < user.password_changed_at:
        raise err_401_not_validate_credentials()

    return user
