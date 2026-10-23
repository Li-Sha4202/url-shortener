import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.config import settings
from src.db.engine import db

from src.features.users.router import router as users_router
from src.features.auth.router import router as auth_router

app = FastAPI()

app.include_router(users_router)
app.include_router(auth_router)


@asynccontextmanager
async def lifespan(app):
    yield
    await db.dispose_engine()  # закрываем пул при выключении


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.run.reload,
    )
