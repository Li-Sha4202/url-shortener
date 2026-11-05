from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    err_400_bad_req_exp_link,
    err_400_reserved_codes,
    err_400_code_exists_in_db,
    err_404_link_not_found,
)

from src.features.links.repository import LinkRepository
from src.features.links.schema import LinkCreate, LinkUpdate
from src.features.links.model import Link

from src.utils.base62 import generate_short_code

RESERVED_CODES = {
    "api",
    "admin",
    "login",
    "auth",
    "links",
    "stats",
    "docs",
    "redoc",
    "openapi.json",
    "create",
    "update",
    "delete",
    "my",
    "top",
    "all",
}


class LinkService:
    """Класс с Бизнес-логикой ссылок"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = LinkRepository(session)

    async def create_link(
        self,
        user_id: int | None,
        data: LinkCreate,
    ) -> Link:
        """Создание ссылки"""

        # 1. Определяем Short_code
        if data.short_code:
            code = data.short_code
            if code in RESERVED_CODES:
                raise err_400_reserved_codes(code)
            if await self.repo.code_exists(code):
                raise err_400_code_exists_in_db(code)
        else:
            code = generate_short_code()

        # 2. Считаем expires_at
        expires_at = None
        if data.expires_at_days:
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=data.expires_at_days
            )

        # 3. Создаём ссылку
        link = await self.repo.create(
            short_code=code,
            original_url=str(data.original_url),
            user_id=user_id,
            expires_at=expires_at,
        )
        await self.session.commit()
        return link

    async def resolve(self, short_code: str) -> str:
        """Редирект: проверка + инкремент + возврат URL"""

        link = await self.repo.get_by_code(short_code)
        if link is None:
            raise err_404_link_not_found(short_code)

        now = datetime.now(timezone.utc)
        if link.expires_at and link.expires_at < now:
            raise err_400_bad_req_exp_link()

        await self.repo.increment_clicks(
            link, now=now, today_iso=now.date().isoformat()
        )

        await self.session.commit()
        return link.original_url

    async def get_user_links(self, user_id: int) -> list[Link]:
        """Получение всех ссылок пользователя"""
        return await self.repo.list_by_user(user_id)

    async def get_user_link(self, user_id: int, short_code: str) -> Link:
        """Получение ссылки пользователя"""
        link = await self.repo.get_by_code_and_user(short_code, user_id)
        if link is None:
            raise err_404_link_not_found(short_code)
        return link

    async def update_link(
        self,
        user_id: int,
        short_code: str,
        data: LinkUpdate,
    ) -> Link:
        """Обновление ссылки"""

        link = await self.repo.get_by_code_and_user(short_code, user_id)
        updates = data.model_dump(exclude_unset=True)

        if link is None:
            raise err_404_link_not_found(short_code)

        if "original_url" in updates:
            updates["original_url"] = str(updates["original_url"])
        if "expires_at_days" in updates:
            days = updates.pop("expires_at_days")
            if days is None or days == -1:
                updates["expires_at"] = None
            else:
                updates["expires_at"] = datetime.now(timezone.utc) + timedelta(
                    days=days
                )

        if not updates:
            return link

        await self.repo.update(link, **updates)
        await self.session.commit()
        return link

    async def delete_link(self, user_id: int, short_code: str) -> None:
        link = await self.get_user_link(user_id, short_code)
        await self.repo.delete(link)
        await self.session.commit()

    async def get_link_stats(self, user_id: int, short_code: str) -> dict:
        """Статистике по одной ссылке"""

        link = await self.repo.get_by_code_and_user(short_code, user_id)

        if link is None:
            raise err_404_link_not_found(short_code)

        return {
            "short_code": link.short_code,
            "clicks_count": link.clicks_count,
            "first_click": link.first_click,
            "last_click": link.last_click,
            "clicks_by_day": link.clicks_by_day or {},
        }

    async def get_global_stats(self) -> dict:
        """Глобальная статистика"""
        return await self.repo.get_global_stats()

    async def get_top_links(self, limit: int = 10):
        """Топ ссылок по кликам"""
        if limit < 1 or limit > 100:
            raise ValueError("Лимит должен быть от 0 до 100")
        return await self.repo.get_top(limit)
