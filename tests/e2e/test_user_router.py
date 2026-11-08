import pytest


class TestRegister:
    async def test_register_success(self, client):
        r = await client.post(
            "/users/register",
            json={
                "name": "alice",
                "email": "alice@example.com",
                "password": "secret123",
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "alice@example.com"
        assert data["name"] == "alice"
        assert data["is_admin"] is False
        assert "password" not in data  # 🔑 пароль не утёк
        assert "id" not in data  # id не отдаём

    async def test_register_duplicate_email(self, client, registered_user):
        r = await client.post(
            "/users/register",
            json={
                "name": "another",
                "email": registered_user["email"],  # уже занят
                "password": "secret123",
            },
        )
        assert r.status_code == 400
        assert "[ID-1]" in r.json()["detail"]

    async def test_register_invalid_email(self, client):
        r = await client.post(
            "/users/register",
            json={
                "name": "alice",
                "email": "not-an-email",
                "password": "secret123",
            },
        )
        assert r.status_code == 422  # Pydantic EmailStr

    async def test_register_short_password(self, client):
        r = await client.post(
            "/users/register",
            json={
                "name": "alice",
                "email": "a@example.com",
                "password": "123",  # < 8
            },
        )
        assert r.status_code == 422

    async def test_register_short_name(self, client):
        r = await client.post(
            "/users/register",
            json={
                "name": "ab",  # < 5
                "email": "a@example.com",
                "password": "secret123",
            },
        )
        assert r.status_code == 422

    async def test_register_password_not_in_db(self, client, db_session):
        """🔑 Пароль в БД — Argon2-хеш, не plaintext."""
        from sqlalchemy import select
        from src.features.users.model import User

        await client.post(
            "/users/register",
            json={
                "name": "alice",
                "email": "alice@example.com",
                "password": "secret123",
            },
        )
        user = (
            await db_session.execute(
                select(User).where(User.email == "alice@example.com")
            )
        ).scalar_one()
        assert user.password != "secret123"
        assert user.password.startswith("$argon2")


class TestReadMe:
    async def test_me_authenticated(self, client, auth_headers, registered_user):
        r = await client.get("/users/me", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["email"] == registered_user["email"]

    async def test_me_unauthorized(self, client):
        r = await client.get("/users/me")
        assert r.status_code == 401

    async def test_me_invalid_token(self, client):
        r = await client.get("/users/me", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401


class TestUpdate:
    async def test_update_name(self, client, auth_headers):
        r = await client.patch(
            "/users/update",
            json={"name": "newname"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["name"] == "newname"

    async def test_update_email_without_password(self, client, auth_headers):
        """🔑 Смена email без current_password → 400 [ID-4]."""
        r = await client.patch(
            "/users/update",
            json={"email": "new@example.com"},
            headers=auth_headers,
        )
        assert r.status_code == 400
        assert "[ID-4]" in r.json()["detail"]

    async def test_update_email_with_correct_password(
        self, client, auth_headers, registered_user
    ):
        r = await client.patch(
            "/users/update",
            json={
                "email": "new@example.com",
                "current_password": registered_user["password"],
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["email"] == "new@example.com"

    async def test_update_email_wrong_password(self, client, auth_headers):
        """🔑 Если verify_password перепутан — этот тест упадёт [ID-5]."""
        r = await client.patch(
            "/users/update",
            json={
                "email": "new@example.com",
                "current_password": "WRONG",
            },
            headers=auth_headers,
        )
        assert r.status_code == 400
        assert "[ID-5]" in r.json()["detail"]

    async def test_update_email_taken(
        self, client, auth_headers, other_user_headers, registered_user
    ):
        """Email занят другим юзером → 400."""
        r = await client.patch(
            "/users/update",
            json={
                "email": "other@example.com",
                "current_password": registered_user["password"],
            },
            headers=auth_headers,
        )
        assert r.status_code == 400

    async def test_update_unauthorized(self, client):
        r = await client.patch("/users/update", json={"name": "hacker"})
        assert r.status_code == 401


class TestChangePassword:
    async def test_change_password_success(self, client, auth_headers, registered_user):
        r = await client.post(
            "/users/update/change-password",
            json={
                "current_password": registered_user["password"],
                "new_password": "newsecret456",
            },
            headers=auth_headers,
        )
        assert r.status_code == 204
        assert r.content == b""  # 🔑 204 = пустое тело

    async def test_change_password_wrong_current(self, client, auth_headers):
        r = await client.post(
            "/users/update/change-password",
            json={
                "current_password": "WRONG",
                "new_password": "newsecret456",
            },
            headers=auth_headers,
        )
        assert r.status_code == 400

    async def test_change_password_short_new(
        self, client, auth_headers, registered_user
    ):
        r = await client.post(
            "/users/update/change-password",
            json={
                "current_password": registered_user["password"],
                "new_password": "123",  # < 8
            },
            headers=auth_headers,
        )
        assert r.status_code == 422

    async def test_change_password_invalidates_old_token(
        self, client, auth_headers, registered_user
    ):
        """🔑 После смены пароля старый токен умирает (password_changed_at)."""
        # Меняем пароль
        r = await client.post(
            "/users/update/change-password",
            json={
                "current_password": registered_user["password"],
                "new_password": "newsecret456",
            },
            headers=auth_headers,
        )
        assert r.status_code == 204

        # Старый токен → 401
        r = await client.get("/users/me", headers=auth_headers)
        assert r.status_code == 401

        # Новый логин с новым паролем работает
        r = await client.post(
            "/auth/login",
            data={"username": registered_user["email"], "password": "newsecret456"},
        )
        assert r.status_code == 200
        new_token = r.json()["access_token"]

        r = await client.get(
            "/users/me", headers={"Authorization": f"Bearer {new_token}"}
        )
        assert r.status_code == 200

    async def test_change_password_unauthorized(self, client):
        r = await client.post(
            "/users/update/change-password",
            json={"current_password": "x", "new_password": "newsecret456"},
        )
        assert r.status_code == 401


class TestDelete:
    async def test_delete_success(self, client, auth_headers, registered_user):
        r = await client.request(
            "DELETE",
            "/users/me/delete",
            json={"current_password": registered_user["password"]},
            headers=auth_headers,
        )
        assert r.status_code == 204
        assert r.content == b""

        # Токен больше не работает
        r = await client.get("/users/me", headers=auth_headers)
        assert r.status_code == 401

    async def test_delete_wrong_password(self, client, auth_headers):
        r = await client.request(
            "DELETE",
            "/users/me/delete",
            json={"current_password": "WRONG"},
            headers=auth_headers,
        )
        assert r.status_code == 400

        # Юзер остался — /me работает
        r = await client.get("/users/me", headers=auth_headers)
        assert r.status_code == 200

    async def test_delete_cascades_links(
        self, client, auth_headers, registered_user, db_session
    ):
        """🔑 Удаление аккаунта → удаление его ссылок."""
        from sqlalchemy import select, func
        from src.features.links.model import Link

        # Создаём ссылку
        r = await client.post(
            "/links/create",
            json={"original_url": "https://example.com"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        code = r.json()["short_code"]

        # Удаляем аккаунт
        r = await client.request(
            "DELETE",
            "/users/me/delete",
            json={"current_password": registered_user["password"]},
            headers=auth_headers,
        )
        assert r.status_code == 204

        # Ссылки больше нет в БД
        count = (
            await db_session.execute(
                select(func.count()).select_from(Link).where(Link.short_code == code)
            )
        ).scalar_one()
        assert count == 0

        # И редирект не работает
        r = await client.get(f"/{code}", follow_redirects=False)
        assert r.status_code == 404

    async def test_delete_unauthorized(self, client):
        r = await client.request(
            "DELETE",
            "/users/me/delete",
            json={
                "current_password": "x",
            },
        )
        assert r.status_code == 401
