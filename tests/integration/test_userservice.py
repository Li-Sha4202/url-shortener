import pytest
from datetime import datetime, timezone
from fastapi import HTTPException

from src.features.users.service import UserService
from src.features.users.repository import UserRepository
from src.features.users.schema import UserUpdateSchema, ChangePasswordSchema
from src.core.security.argon_hasher import verify_password


@pytest.fixture
async def service(db_session) -> UserService:
    return UserService(session=db_session)


class TestUserService:

    # -- Create User --
    async def test_create_user_success(self, service):
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        assert user.id is not None
        assert user.email == "alice@example.com"
        assert user.name == "alice"

    async def test_create_user_password_is_hashed(self, service, db_session):
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        await db_session.refresh(user)

        assert user.password != "secret123"
        assert user.password.startswith("$argon2")
        assert verify_password(user.password, "secret123")
        assert not verify_password("wrongpass", user.password)

    async def test_create_user_duplicate_email(self, service):
        await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        with pytest.raises(HTTPException) as exc:
            await service.create_user(
                name="bob", email="alice@example.com", password="other123"
            )
        assert exc.value.status_code == 400
        assert "alice@example.com" in exc.value.detail

    async def test_create_user_password_changed_at_set(self, service, db_session):
        """password_changed_at выставляется при создании."""
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        await db_session.refresh(user)
        assert user.password_changed_at is not None
        assert isinstance(user.password_changed_at, datetime)

    # -- Update Account --
    async def test_update_name_only(self, service):
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        updated = await service.update_account(
            user.id, UserUpdateSchema(name="alice_new")
        )
        assert updated.name == "alice_new"
        assert updated.email == "alice@example.com"  # не тронуто

    async def test_update_email_requires_password(self, service):
        """🔑 Смена email без current_password → 400."""
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        with pytest.raises(HTTPException) as exc:
            await service.update_account(
                user.id, UserUpdateSchema(email="new@example.com")
            )
        assert exc.value.status_code == 400
        assert "пароль" in exc.value.detail.lower()

    async def test_update_email_with_correct_password(self, service):
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        updated = await service.update_account(
            user.id,
            UserUpdateSchema(email="new@example.com", current_password="secret123"),
        )
        assert updated.email == "new@example.com"

    async def test_update_email_wrong_password(self, service):
        """🔑 Если verify_password перепутан — этот тест упадёт."""
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        with pytest.raises(HTTPException) as exc:
            await service.update_account(
                user.id,
                UserUpdateSchema(email="new@example.com", current_password="WRONG"),
            )
        assert exc.value.status_code == 400

    async def test_update_email_taken(self, service):
        await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        bob = await service.create_user(
            name="bob", email="bob@example.com", password="secret123"
        )
        with pytest.raises(HTTPException) as exc:
            await service.update_account(
                bob.id,
                UserUpdateSchema(
                    email="alice@example.com", current_password="secret123"
                ),
            )
        assert exc.value.status_code == 400

    async def test_update_email_same_email(self, service):
        """Смена email на тот же — не требует пароля (нет реального изменения)."""
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        updated = await service.update_account(
            user.id, UserUpdateSchema(email="alice@example.com")
        )
        assert updated.email == "alice@example.com"

    async def test_update_empty_payload(self, service):
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        updated = await service.update_account(user.id, UserUpdateSchema())
        assert updated.name == "alice"
        assert updated.email == "alice@example.com"

    async def test_update_user_not_found(self, service):
        with pytest.raises(HTTPException) as exc:
            await service.update_account(999_999, UserUpdateSchema(name="ghost"))
        assert exc.value.status_code == 401

    # -- Change Password --
    async def test_change_password_success(self, service, db_session):
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        old_hash = user.password

        await service.change_password(
            user.id,
            ChangePasswordSchema(
                current_password="secret123", new_password="newsecret456"
            ),
        )
        await db_session.refresh(user)

        assert user.password != old_hash  # хеш сменился
        assert verify_password(user.password, "newsecret456")  # новый работает
        assert not verify_password(user.password, "secret123")  # старый нет

    async def test_change_password_updates_timestamp(self, service, db_session):
        """🔑 password_changed_at меняется — это основа инвалидации токенов."""
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        await db_session.refresh(user)
        old_ts = user.password_changed_at

        # Пауза, чтобы timestamp точно был другим (на медленных дисках)
        import asyncio

        await asyncio.sleep(0.01)

        await service.change_password(
            user.id,
            ChangePasswordSchema(
                current_password="secret123", new_password="newsecret456"
            ),
        )
        await db_session.refresh(user)

        assert user.password_changed_at > old_ts

    async def test_change_password_wrong_current(self, service):
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        with pytest.raises(HTTPException) as exc:
            await service.change_password(
                user.id,
                ChangePasswordSchema(
                    current_password="WRONG", new_password="newsecret456"
                ),
            )
        assert exc.value.status_code == 400

    async def test_change_password_user_not_found(self, service):
        with pytest.raises(HTTPException) as exc:
            await service.change_password(
                999_999,
                ChangePasswordSchema(current_password="x", new_password="newsecret456"),
            )
        assert exc.value.status_code == 401

    # -- Delete Account --
    async def test_delete_account_success(self, service):
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        user_id = user.id

        await service.delete_account(user_id, "secret123")

        repo = UserRepository(service.session)
        assert await repo.get_by_id(user_id) is None

    async def test_delete_account_wrong_password(self, service):
        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        with pytest.raises(HTTPException) as exc:
            await service.delete_account(user.id, "WRONG")
        assert exc.value.status_code == 400

        # Юзер должен остаться
        repo = UserRepository(service.session)
        assert await repo.get_by_id(user.id) is not None

    async def test_delete_account_cascades_links(self, service, db_session):
        """🔑 Удаление user → удаление его links (ondelete=CASCADE)."""
        from src.features.links.model import Link

        user = await service.create_user(
            name="alice", email="alice@example.com", password="secret123"
        )
        link = Link(short_code="abc", original_url="https://x.com", user_id=user.id)
        db_session.add(link)
        await db_session.flush()

        await service.delete_account(user.id, "secret123")

        from sqlalchemy import select, func

        count = (
            await db_session.execute(
                select(func.count()).select_from(Link).where(Link.user_id == user.id)
            )
        ).scalar_one()
        assert count == 0
