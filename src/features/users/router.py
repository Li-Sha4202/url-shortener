from fastapi import APIRouter, Depends, status

from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import get_session

from .service import UserService
from .schema import UserCreateSchema, UserResponseSchema
from .dependencies import get_user_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def user_register(
    data: UserCreateSchema,
    service: UserService = Depends(get_user_service),
):
    """Регистрация пользователя."""

    user = await service.create_user(
        email=data.email,
        name=data.name,
        password=data.password,
    )
    return user
