from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/register")
async def user_register():
    """Регистрация пользователя."""
    pass
