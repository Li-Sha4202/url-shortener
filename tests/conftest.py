import pytest
from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from src.db.base import Base
from src.db.engine import get_session

from src.features.links.service import LinkService
from src.features.users.model import User

from src.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@test-db:5432/test_db"
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db_session():
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
async def client(db_session: AsyncSession):
    """HTTP-клиент с подменённой БД."""

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def user(db_session) -> User:
    u = User(
        name="testuser",
        email="test@example.com",
        password="fake_hash_for_tests",  # хэш не важен для тестов ссылок
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.fixture
async def other_user(db_session) -> User:
    u = User(
        name="otheruser",
        email="other@example.com",
        password="fake_hash_for_tests",
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.fixture
async def service(db_session) -> LinkService:
    return LinkService(session=db_session)
