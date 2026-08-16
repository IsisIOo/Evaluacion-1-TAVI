"""Tests para app/api/v1/auth_endpoint.py: registro y login."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import get_db


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def fake_db():
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    yield db
    app.dependency_overrides.clear()


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_creates_user(self, client, fake_db):
        fake_repo = AsyncMock()
        fake_repo.get_by_email.return_value = None

        created_user = MagicMock()
        created_user.id = "507f1f77bcf86cd799439011"
        created_user.email = "new@example.com"
        created_user.nombre = "Nuevo Usuario"
        created_user.is_active = True
        fake_repo.create_user.return_value = created_user

        with patch("app.api.v1.auth_endpoint.UserRepository", return_value=fake_repo):
            response = await client.post(
                "/api/auth/register",
                json={
                    "email": "new@example.com",
                    "password": "clave123",
                    "nombre": "Nuevo Usuario",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        fake_repo.create_user.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_rejects_duplicate_email(self, client, fake_db):
        existing = MagicMock()
        existing.email = "dup@example.com"

        fake_repo = AsyncMock()
        fake_repo.get_by_email.return_value = existing

        with patch("app.api.v1.auth_endpoint.UserRepository", return_value=fake_repo):
            response = await client.post(
                "/api/auth/register",
                json={
                    "email": "dup@example.com",
                    "password": "clave123",
                    "nombre": "Dup",
                },
            )

        assert response.status_code == 400
        assert "ya está registrado" in response.json()["detail"]
        fake_repo.create_user.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_register_validation_error(self, client, fake_db):
        response = await client.post(
            "/api/auth/register",
            json={"email": "no-es-email", "password": "123", "nombre": "X"},
        )
        assert response.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client, fake_db):
        from app.core.security import get_password_hash

        user = MagicMock()
        user.id = "507f1f77bcf86cd799439011"
        user.password_hash = get_password_hash("clave123")

        fake_repo = AsyncMock()
        fake_repo.get_by_email.return_value = user

        with patch("app.api.v1.auth_endpoint.UserRepository", return_value=fake_repo):
            response = await client.post(
                "/api/auth/login",
                data={"username": "test@example.com", "password": "clave123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, fake_db):
        from app.core.security import get_password_hash

        user = MagicMock()
        user.id = "507f1f77bcf86cd799439011"
        user.password_hash = get_password_hash("clave-correcta")

        fake_repo = AsyncMock()
        fake_repo.get_by_email.return_value = user

        with patch("app.api.v1.auth_endpoint.UserRepository", return_value=fake_repo):
            response = await client.post(
                "/api/auth/login",
                data={"username": "test@example.com", "password": "clave-mala"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, client, fake_db):
        fake_repo = AsyncMock()
        fake_repo.get_by_email.return_value = None

        with patch("app.api.v1.auth_endpoint.UserRepository", return_value=fake_repo):
            response = await client.post(
                "/api/auth/login",
                data={"username": "ghost@example.com", "password": "clave123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        assert response.status_code == 401
