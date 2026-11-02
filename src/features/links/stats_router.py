from fastapi import APIRouter, Depends, Query

from src.features.auth.dependencies import get_current_user, get_current_admin_user
from src.features.users.model import User

from src.features.links.dependencies import get_link_service
from src.features.links.schema import LinkStats, LinkStatsAll, LinkStatsTop
from src.features.links.service import LinkService

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/global", response_model=LinkStatsAll)
async def global_stats(
    current_admin: User = Depends(get_current_admin_user),
    service: LinkService = Depends(get_link_service),
):
    """Общая статистика"""
    return await service.get_global_stats()


@router.get("/top", response_model=list[LinkStatsTop])
async def top_links(
    limit: int = Query(10, ge=1, le=100),
    current_admin: User = Depends(get_current_admin_user),
    service: LinkService = Depends(get_link_service),
):
    """Топ Ссылок"""
    return await service.get_top_links(limit)


@router.get("/links/{short_code}", response_model=LinkStats)
async def link_stats(
    short_code: str,
    current_user: User = Depends(get_current_user),
    service: LinkService = Depends(get_link_service),
):
    """Получение статистики по своей ссылке"""
    return await service.get_link_stats(current_user.id, short_code)
