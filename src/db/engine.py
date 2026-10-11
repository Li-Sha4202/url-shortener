from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings


class DataBaseEngine:
    """Двигатель Базы данных"""

    def __init__(
        self,
        url: str,
        echo: bool,
        pool_size: int,
        max_overflow: int,
        pool_pre_ping: bool,
        pool_recycle: int,
        expire_on_commit: bool,
        autoflush: bool,
    ) -> None:
        self.engine = create_async_engine(  # Создание движка
            url=url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            pool_recycle=pool_recycle,
        )

        self.session_factory = async_sessionmaker(  # Создание фабрики сессий
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=expire_on_commit,
            autoflush=autoflush,
        )

    async def dispose_engine(self) -> None:
        await self.engine.dispose()


db = DataBaseEngine(
    url=str(settings.db.url),
    echo=settings.db.echo,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
    pool_pre_ping=settings.db.pool_pre_ping,
    pool_recycle=settings.db.pool_recycle,
    expire_on_commit=settings.db.expire_on_commit,
    autoflush=settings.db.autoflush,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with db.session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
