from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import get_session

from src.core.security.jwt_token import create_access_token
from src.core.security.argon_hasher import verify_password

from src.core.exceptions import err_401_not_authentificated

from src.features.auth.schema import Token

from src.features.users.repository import UserRepository

router = APIRouter(prefix="auth", tags=["auth"])


@router.post(
    "/login",
    response_model=Token,
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    """Аутентификация пользователя и получение токена"""
    repo = UserRepository(session)

    user = await repo.get_by_name(form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise err_401_not_authentificated()

    access_token = create_access_token(user_id=user.id)
    return Token(access_token=access_token)
