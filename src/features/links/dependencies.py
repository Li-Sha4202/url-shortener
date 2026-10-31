from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import get_session

from src.features.links.service import LinkService


def get_link_service(
    session: AsyncSession = Depends(get_session),
) -> LinkService:
    """DI для сервиса"""
    return LinkService(session)
