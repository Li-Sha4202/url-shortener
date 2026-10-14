from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.users.model import User


class UserRepository:
    """Класс с SQL-логикой для User"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, username: str, password: bytes, email: str) -> User:
        """Создание пользователя"""
        stmt = User(
            email=email,
            username=username,
            password=password,
        )
        self.session.add(stmt)
        await self.session.flush()
        return stmt

    async def get_by_email(self, email: str) -> User | None:
        """Поиск пользователя по почте"""

        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, username: str) -> User | None:
        """Поиск пользователя по имени"""

        stmt = select(User).where(User.name == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
