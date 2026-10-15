from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import get_session

from src.features.users.service import UserService


def get_user_service(
    session: AsyncSession = Depends(get_session),
) -> UserService:
    """DI для сервиса"""
    return UserService(session)
