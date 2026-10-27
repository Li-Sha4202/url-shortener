from fastapi import APIRouter, Depends, status

from src.features.users.service import UserService
from src.features.users.schema import (
    UserCreateSchema,
    UserResponseSchema,
    UserUpdateSchema,
    ChangePasswordSchema,
    AccountDelete,
)
from src.features.users.dependencies import get_user_service

from src.features.auth.dependencies import get_current_user

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


@router.get("/me", response_model=UserResponseSchema)
async def read_user_me(current_user=Depends(get_current_user)):
    """Возвращает данные о текущем аутентифицированном пользователе"""
    return current_user


@router.patch("/update", response_model=UserResponseSchema)
async def update_me(
    data: UserUpdateSchema,
    current_user=Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await service.update_account(current_user.id, data=data)


@router.post(
    "/update/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def change_password(
    data: ChangePasswordSchema,
    current_user=Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    await service.change_password(current_user.id, data=data)


@router.delete(
    "/me/delete",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_me(
    data: AccountDelete,
    current_user=Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    await service.delete_account(current_user.id, data.current_password)
