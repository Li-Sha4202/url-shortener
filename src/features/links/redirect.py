from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse

from src.features.links.service import LinkService
from src.features.links.dependencies import get_link_service

router = APIRouter(tags=["redirect"])


@router.get("/{short_code}")
async def redirect(
    short_code: str,
    service: LinkService = Depends(get_link_service),
):
    """Редирект по ссылке"""
    target = await service.resolve(short_code)
    return RedirectResponse(
        url=target,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
