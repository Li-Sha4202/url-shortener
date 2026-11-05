# tests/integration/test_link_service.py
import pytest
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from src.features.links.schema import LinkCreate, LinkUpdate
from src.features.links.repository import LinkRepository


class TestLinkService:

    # -- Создание --
    async def test_create_link_minimal(self, service, user):
        link = await service.create_link(
            user.id, LinkCreate(original_url="https://example.com")
        )
        assert link.id is not None
        assert link.short_code
        assert link.user_id == user.id
        assert link.expires_at is None
        assert link.clicks_count == 0

        # Проверяем, что реально в БД
        repo = LinkRepository(service.session)
        fetched = await repo.get_by_code(link.short_code)
        assert fetched is not None
        assert fetched.id == link.id

    async def test_create_link_with_expiration(self, service, user):
        before = datetime.now(timezone.utc)
        link = await service.create_link(
            user.id,
            LinkCreate(original_url="https://example.com", expires_at_days=10),
        )
        after = datetime.now(timezone.utc)

        assert link.expires_at is not None
        # Проверяем, что дата ≈ now + 10 дней (допуск 2 секунды на выполнение)
        assert (
            before + timedelta(days=10, seconds=-2)
            <= link.expires_at
            <= after + timedelta(days=10, seconds=2)
        )

    async def test_create_link_custom_code(self, service, user):
        link = await service.create_link(
            user.id,
            LinkCreate(original_url="https://example.com", short_code="mycode"),
        )
        assert link.short_code == "mycode"

    async def test_create_link_reserved_code(self, service, user):
        with pytest.raises(HTTPException) as exc:
            await service.create_link(
                user.id,
                LinkCreate(original_url="https://example.com", short_code="delete"),
            )
        assert exc.value.status_code == 400

    async def test_create_link_duplicate_code(self, service, user):
        await service.create_link(
            user.id, LinkCreate(original_url="https://a.com", short_code="duppy")
        )
        with pytest.raises(HTTPException) as exc:
            await service.create_link(
                user.id, LinkCreate(original_url="https://b.com", short_code="duppy")
            )
        assert exc.value.status_code == 400

    async def test_create_link_anonymous(self, service):
        link = await service.create_link(
            user_id=None,
            data=LinkCreate(original_url="https://example.com"),
        )
        assert link.user_id is None

    # -- Resolve --
    async def test_resolve_returns_url(self, service, user):
        link = await service.create_link(
            user.id, LinkCreate(original_url="https://example.com")
        )
        url = await service.resolve(link.short_code)
        assert url == "https://example.com/"

    async def test_resolve_not_found(self, service):
        with pytest.raises(HTTPException) as exc:
            await service.resolve("doesnotexist")
        assert exc.value.status_code == 404

    async def test_resolve_increments_clicks(self, service, user):
        link = await service.create_link(
            user.id, LinkCreate(original_url="https://example.com")
        )
        await service.resolve(link.short_code)
        await service.resolve(link.short_code)

        await service.session.refresh(link)  # ← перечитываем из БД
        assert link.clicks_count == 2
        assert link.first_click is not None
        assert link.last_click is not None
        today = datetime.now(timezone.utc).date().isoformat()
        assert link.clicks_by_day == {today: 2}

    async def test_resolve_expired_link(self, service, user):
        """Ссылка с истёкшим expires_at — должна не резолвиться."""
        link = await service.create_link(
            user.id, LinkCreate(original_url="https://example.com")
        )
        # Вручную ставим истёкший срок
        link.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        await service.session.flush()

        with pytest.raises(HTTPException):
            await service.resolve(link.short_code)

    # -- Обновление --
    async def test_update_url(self, service, user):
        link = await service.create_link(
            user.id, LinkCreate(original_url="https://old.com")
        )
        updated = await service.update_link(
            user.id, link.short_code, LinkUpdate(original_url="https://new.com/")
        )
        assert updated.original_url == "https://new.com/"

    async def test_update_expiration_set(self, service, user):
        link = await service.create_link(
            user.id, LinkCreate(original_url="https://example.com")
        )
        updated = await service.update_link(
            user.id, link.short_code, LinkUpdate(expires_at_days=30)
        )
        assert updated.expires_at is not None

    async def test_update_expiration_clear(self, service, user):
        """-1 = сделать бессрочной."""
        link = await service.create_link(
            user.id,
            LinkCreate(original_url="https://example.com", expires_at_days=10),
        )
        updated = await service.update_link(
            user.id, link.short_code, LinkUpdate(expires_at_days=-1)
        )
        assert updated.expires_at is None

    async def test_update_not_owner(self, service, user, other_user):
        link = await service.create_link(
            user.id, LinkCreate(original_url="https://example.com")
        )
        with pytest.raises(HTTPException) as exc:
            await service.update_link(
                other_user.id,
                link.short_code,
                LinkUpdate(original_url="https://evil.com"),
            )
        assert exc.value.status_code == 404

    async def test_update_empty_payload(self, service, user):
        link = await service.create_link(
            user.id, LinkCreate(original_url="https://example.com")
        )
        original_updated = link.updated_at if hasattr(link, "updated_at") else None
        same_link = await service.update_link(user.id, link.short_code, LinkUpdate())
        assert same_link.original_url == "https://example.com/"

    # -- Удаление --
    async def test_delete_link(self, service, user):
        link = await service.create_link(
            user.id, LinkCreate(original_url="https://example.com")
        )
        await service.delete_link(user.id, link.short_code)

        repo = LinkRepository(service.session)
        assert await repo.get_by_code(link.short_code) is None

    async def test_delete_not_owner(self, service, user, other_user):
        link = await service.create_link(
            user.id, LinkCreate(original_url="https://example.com")
        )
        with pytest.raises(HTTPException) as exc:
            await service.delete_link(other_user.id, link.short_code)
        assert exc.value.status_code == 404

    # -- Статистика --
    async def test_get_link_stats(self, service, user):
        link = await service.create_link(
            user.id, LinkCreate(original_url="https://example.com")
        )
        await service.resolve(link.short_code)
        await service.resolve(link.short_code)

        stats = await service.get_link_stats(user.id, link.short_code)
        assert stats["clicks_count"] == 2
        assert stats["first_click"] is not None
        today = datetime.now(timezone.utc).date().isoformat()
        assert stats["clicks_by_day"][today] == 2

    async def test_get_link_stats_not_owner(self, service, user, other_user):
        link = await service.create_link(
            user.id, LinkCreate(original_url="https://example.com")
        )
        with pytest.raises(HTTPException) as exc:
            await service.get_link_stats(other_user.id, link.short_code)
        assert exc.value.status_code == 404

    async def test_get_global_stats(self, service, user):
        for i in range(3):
            l = await service.create_link(
                user.id, LinkCreate(original_url=f"https://e{i}.com")
            )
        await service.resolve((await service.get_user_links(user.id))[0].short_code)

        stats = await service.get_global_stats()
        assert stats["total_links"] == 3
        assert stats["total_clicks"] == 1

    async def test_get_top_links_order(self, service, user):
        links = []
        for i in range(3):
            links.append(
                await service.create_link(
                    user.id, LinkCreate(original_url=f"https://e{i}.com")
                )
            )
        await service.resolve(links[0].short_code)
        await service.resolve(links[1].short_code)
        await service.resolve(links[2].short_code)

        top = await service.get_top_links(limit=10)
        assert len(top) == 3
        assert top[0].short_code == links[0].short_code
        assert top[1].short_code == links[1].short_code
        assert top[2].short_code == links[2].short_code

    # -- Валидация --
    async def test_get_top_links_invalid_limit(self, service):
        with pytest.raises(ValueError):
            await service.get_top_links(limit=0)
        with pytest.raises(ValueError):
            await service.get_top_links(limit=101)
