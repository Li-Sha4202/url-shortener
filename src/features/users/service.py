from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import err_400_user_already_exists
from src.core.security.argon_hasher import password_hash, verify_password, DUMMY_HASH

from src.features.users.model import User
from src.features.users.repository import UserRepository


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
            verify_password(password, DUMMY_HASH)
            raise err_400_user_already_exists(email)

        hashed_password = password_hash(password)

        user = await self.repo.create_user(
            name=name,
            password=hashed_password,
            email=email,
        )

        await self.session.commit()
        return user
