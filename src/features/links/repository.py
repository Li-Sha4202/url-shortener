from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, update

from src.features.links.model import Link


class LinkRepository:
    """Класс с SQL-запросами для Link"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # === Чтение ===

    async def get_by_code(self, code: str) -> Link | None:
        """Получение ссылки по его короткому коду"""
        stmt = select(Link).where(Link.short_code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code_and_user(self, short_code: str, user_id: int) -> Link | None:
        """Для операций, где нужна проверка пользователя"""
        stmt = select(Link).where(
            Link.short_code == short_code, Link.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def code_exists(self, short_code: str) -> bool:
        stmt = (
            select(func.count()).select_from(Link).where(Link.short_code == short_code)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def list_by_user(self, user_id: int) -> list[Link]:
        """Получение списка всех ссылок пользователя"""
        stmt = select(Link).where(Link.user_id == user_id).order_by(Link.id.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, limit: int = 100) -> list[Link]:
        """Получение всех ссылок"""

        stmt = select(Link).order_by(Link.id).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # === Запись ===

    async def create(
        self,
        short_code: str,
        original_url: str,
        user_id: int | None,
        expires_at: datetime | None,
    ) -> Link:
        """Создание ссылки"""

        link = Link(
            short_code=short_code,
            original_url=original_url,
            user_id=user_id,
            expires_at=expires_at,
        )
        self.session.add(link)
        await self.session.flush()
        return link

    async def update(self, link: Link, **fields) -> Link:
        """Обновление ссылки"""
        for key, value in fields.items():
            setattr(link, key, value)
        await self.session.flush()
        return link

    async def delete(self, link: Link) -> None:
        """Удаление ссылки"""
        await self.session.delete(link)
        await self.session.flush()

    # === Статистика ===

    async def increment_clicks(
        self,
        link: Link,
        now: datetime,
        today_iso: str,
    ) -> None:
        """Атомарное обновление счётчиков"""

        link.clicks_count += 1
        if link.first_click is None:
            link.first_click = now
        link.last_click = now

        day_data = dict(link.clicks_by_day) if link.clicks_by_day else {}
        day_data[today_iso] = day_data.get(today_iso, 0) + 1
        link.clicks_by_day = day_data
        await self.session.flush()

    async def get_global_stats(self) -> dict:
        """Получение общей статистики по всем ссылкам"""

        now = datetime.now(timezone.utc)

        total_clicks = await self.session.execute(
            select(func.sum(Link.clicks_count)).select_from(Link)
        )
        total_clicks_sum = total_clicks.scalar_one()

        total_links = await self.session.execute(
            select(func.count()).select_from(Link),
        )
        total_links_count = total_links.scalar_one()

        active_links = await self.session.execute(
            select(func.count()).where(
                Link.expires_at.is_(None) | (Link.expires_at > now),
            )
        )
        active_links_count = active_links.scalar_one()
        expired_links_count = total_links_count - active_links_count
        return {
            "total_clicks": total_clicks_sum,
            "total_links": total_links_count,
            "active_links": active_links_count,
            "expired_links": expired_links_count,
        }

    async def get_top(self, limit: int) -> list[Link]:
        """Получение топ-(число) популярных ссылок"""
        stmt = (
            select(Link)
            .where(Link.clicks_count > 0)
            .order_by(Link.clicks_count.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
