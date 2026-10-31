from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse

from src.features.auth.dependencies import get_current_user
from src.features.users.model import User

from src.features.links.service import LinkService
from src.features.links.dependencies import get_link_service
from src.features.links.schema import LinkCreate, LinkResponse, LinkUpdate

router = APIRouter(prefix="/links", tags=["Links"])


@router.post(
    "/create", response_model=LinkResponse, status_code=status.HTTP_201_CREATED
)
async def create(
    data: LinkCreate,
    current_user: User | None = Depends(get_current_user),
    service: LinkService = Depends(get_link_service),
):
    """Создание ссылки"""
    link = await service.create_link(
        user_id=current_user.id if current_user else None,
        data=data,
    )
    return link


@router.get("/my", response_model=list[LinkResponse])
async def my_links(
    current_user: User = Depends(get_current_user),
    service: LinkService = Depends(get_link_service),
):
    """Список ссылок пользователя"""
    return await service.get_user_links(user_id=current_user.id)


@router.patch("/{short_code}/update", response_model=LinkResponse)
async def update(
    short_code: str,
    data: LinkUpdate,
    current_user: User = Depends(get_current_user),
    service: LinkService = Depends(get_link_service),
):
    """Обновление данных о ссылке"""
    return await service.update_link(
        current_user.id,
        short_code=short_code,
        data=data,
    )


@router.delete("/{short_code}/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    short_code: str,
    current_user: User = Depends(get_current_user),
    service: LinkService = Depends(get_link_service),
):
    """Удаление ссылки"""
    return await service.delete_link(
        user_id=current_user.id,
        short_code=short_code,
    )
