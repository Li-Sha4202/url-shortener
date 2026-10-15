from fastapi import APIRouter

from .router import router as user_router

routers = APIRouter(prefix="/users", tags=["Users"])

routers.include_router(user_router)
