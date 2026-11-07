class TestLinkRouter:

    # -- Create Router --
    async def test_create_link_anonymous(self, client, db_session):
        r = await client.post(
            "/links/create",
            json={
                "original_url": "https://example.com",
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["short_code"]
        assert data["short_url"].endswith(data["short_code"])
        assert data["expires_at"] is None
        # Проверяем в БД, что user_id = None
        from src.features.links.model import Link
        from sqlalchemy import select

        link = (
            await db_session.execute(
                select(Link).where(Link.short_code == data["short_code"])
            )
        ).scalar_one()
        assert link.user_id is None

    async def test_create_link_authenticated(self, client, auth_headers, db_session):
        r = await client.post(
            "/links/create",
            json={"original_url": "https://example.com"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        # Проверяем, что user_id привязался
        from src.features.links.model import Link
        from sqlalchemy import select

        link = (
            await db_session.execute(
                select(Link).where(Link.short_code == r.json()["short_code"])
            )
        ).scalar_one()
        assert link.user_id is not None

    async def test_create_link_with_expiration(self, client, auth_headers):
        r = await client.post(
            "/links/create",
            json={"original_url": "https://example.com", "expires_at_days": 10},
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert r.json()["expires_at"] is not None

    async def test_create_link_reserved_code(self, client, auth_headers):
        r = await client.post(
            "/links/create",
            json={"original_url": "https://example.com", "short_code": "admin"},
            headers=auth_headers,
        )
        assert r.status_code == 400

    async def test_create_link_invalid_url(self, client, auth_headers):
        r = await client.post(
            "/links/create",
            json={"original_url": "not-a-url"},
            headers=auth_headers,
        )
        assert r.status_code == 422

    async def test_create_link_invalid_expiration(self, client, auth_headers):
        r = await client.post(
            "/links/create",
            json={"original_url": "https://example.com", "expires_at_days": 400},
            headers=auth_headers,
        )
        assert r.status_code == 422

    # -- Redirect --
    async def test_redirect_returns_307(self, client, auth_headers):
        """🔑 Тот самый баг с портом: проверяем Location."""
        r = await client.post(
            "/links/create",
            json={"original_url": "https://github.com/features"},
            headers=auth_headers,
        )
        code = r.json()["short_code"]

        r = await client.get(f"/{code}", follow_redirects=False)  # ← не следовать!
        assert r.status_code == 307
        assert r.headers["location"] == "https://github.com/features"

    async def test_redirect_not_found(self, client):
        r = await client.get("/doesnotexist", follow_redirects=False)
        assert r.status_code == 404

    async def test_redirect_expired(self, client, auth_headers, db_session):
        """Истёкшая ссылка — 400 (или 410, если поправишь)."""
        from datetime import datetime, timedelta, timezone
        from src.features.links.model import Link
        from sqlalchemy import select

        r = await client.post(
            "/links/create",
            json={"original_url": "https://example.com"},
            headers=auth_headers,
        )
        code = r.json()["short_code"]

        # Ставим expires_at в прошлое
        link = (
            await db_session.execute(select(Link).where(Link.short_code == code))
        ).scalar_one()
        link.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        await db_session.flush()

        r = await client.get(f"/{code}", follow_redirects=False)
        assert r.status_code == 400

    # -- My Links --
    async def test_my_links_only_own(
        self, client, auth_headers, other_user, db_session
    ):
        # Создаём две ссылки от этого юзера
        for url in ("https://a.com", "https://b.com"):
            await client.post(
                "/links/create",
                json={"original_url": url},
                headers=auth_headers,
            )

        # Создаём чужую ссылку (другой user_id напрямую в БД)
        from src.features.links.model import Link

        db_session.add(
            Link(
                short_code="other",
                original_url="https://other.com",
                user_id=other_user.id,
            )
        )
        await db_session.flush()

        r = await client.get("/links/my", headers=auth_headers)
        assert r.status_code == 200
        codes = [item["short_code"] for item in r.json()]
        assert "other" not in codes
        assert len(codes) == 2

    async def test_my_links_unauthorized(self, client):
        r = await client.get("/links/my")
        assert r.status_code == 401

    # -- Update --
    async def test_update_link_success(self, client, auth_headers):
        r = await client.post(
            "/links/create",
            json={"original_url": "https://old.com"},
            headers=auth_headers,
        )
        code = r.json()["short_code"]

        r = await client.patch(
            f"/links/{code}/update",
            json={"original_url": "https://new.com"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["original_url"] == "https://new.com/"

    async def test_update_link_not_owner(
        self, client, auth_headers, other_user, db_session
    ):
        from src.features.links.model import Link

        db_session.add(
            Link(
                short_code="other",
                original_url="https://x.com",
                user_id=other_user.id,
            )
        )
        await db_session.flush()

        r = await client.patch(
            "/links/other/update",
            json={"original_url": "https://hack.com"},
            headers=auth_headers,
        )
        assert r.status_code == 404

    async def test_update_link_clear_expiration(self, client, auth_headers):
        r = await client.post(
            "/links/create",
            json={"original_url": "https://example.com", "expires_at_days": 10},
            headers=auth_headers,
        )
        code = r.json()["short_code"]

        r = await client.patch(
            f"/links/{code}/update",
            json={"expires_at_days": -1},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["expires_at"] is None

    async def test_update_link_unauthorized(self, client):
        r = await client.patch(
            "/links/anycode/update", json={"original_url": "https://x.com"}
        )
        assert r.status_code == 401

    # -- Delete --
    async def test_delete_link_success(self, client, auth_headers):
        r = await client.post(
            "/links/create",
            json={"original_url": "https://example.com"},
            headers=auth_headers,
        )
        code = r.json()["short_code"]

        r = await client.delete(f"/links/{code}/delete", headers=auth_headers)
        assert r.status_code == 204
        assert r.content == b""  # 🔑 204 = пустое тело

        # Ссылка больше не резолвится
        r = await client.get(f"/{code}", follow_redirects=False)
        assert r.status_code == 404

    async def test_delete_link_not_owner(
        self, client, auth_headers, other_user, db_session
    ):
        from src.features.links.model import Link

        db_session.add(
            Link(
                short_code="other",
                original_url="https://x.com",
                user_id=other_user.id,
            )
        )
        await db_session.flush()

        r = await client.delete("/links/other/delete", headers=auth_headers)
        assert r.status_code == 404
