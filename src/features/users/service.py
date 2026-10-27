from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    err_400_user_already_exists,
    err_401_not_authentificated,
    err_400_invalid_password,
    err_400_requied_current_password,
)
from src.core.security.argon_hasher import password_hash, verify_password, DUMMY_HASH

from src.features.users.model import User
from src.features.users.repository import UserRepository
from src.features.users.schema import UserUpdateSchema, ChangePasswordSchema


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

    async def update_account(self, user_id: int, data: UserUpdateSchema) -> User:
        """Обновление аккаунта"""

        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise err_401_not_authentificated()

        update = data.model_dump(exclude_unset=True)

        current_password = update.pop("current_password", None)

        if "email" in update and update["email"] != user.email:
            if not current_password:
                raise err_400_requied_current_password()
            if not verify_password(user.password, current_password):
                raise err_400_invalid_password()

            existing = await self.repo.get_by_email(update["email"])
            if existing is not None and existing.id != user.id:
                raise err_400_user_already_exists(update["email"])

        if not update:
            return user

        user = await self.repo.update(user, **update)
        await self.session.commit()
        return user

    async def change_password(self, user_id: int, data: ChangePasswordSchema):
        """Изменение пароля"""

        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise err_401_not_authentificated()

        if not verify_password(user.password, data.current_password):
            raise err_400_invalid_password()

        hashed = password_hash(data.new_password)
        await self.repo.update(
            user,
            password=hashed,
            password_changed_at=datetime.now(timezone.utc),
        )
        await self.session.commit()
        return user

    async def delete_account(self, user_id: int, current_password: str):
        """Удаление аккаунта"""

        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise err_401_not_authentificated()

        if not verify_password(user.password, current_password):
            raise err_400_invalid_password()

        await self.repo.delete(user)
        await self.session.commit()
