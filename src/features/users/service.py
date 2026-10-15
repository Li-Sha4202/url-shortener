from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import err_400_user_already_exists

from features.users.model import User
from features.users.repository import UserRepository


class UserService:
    """Класс с Бизнес-логикой пользователей"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserRepository(session)

    async def create_user(
        self,
        name: str,
        email: str,
        password: str,
    ) -> User:
        """Создание нового пользователя"""

        result = await self.repo.get_by_email(email=email)
        if result is not None:
            raise err_400_user_already_exists(email)

        user = await self.repo.create_user(
            name=name,
            password=password,
            email=email,
        )

        await self.session.commit()
        return user
