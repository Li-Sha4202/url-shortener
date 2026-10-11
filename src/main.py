import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import settings
from db.engine import db

app = FastAPI()


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
