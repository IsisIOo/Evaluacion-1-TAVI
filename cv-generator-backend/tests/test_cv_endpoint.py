"""Tests para app/api/v1/cv_endpoint.py: generación y consulta de CVs con autenticación."""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.dependencies import get_current_user, get_current_user_optional
from app.services.llm_service import QuotaExceededError


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _override_auth(fake_user):
    """Retorna un override para get_current_user que devuelve fake_user."""
    return lambda: fake_user


class TestGenerateCvEndpoint:
    @pytest.mark.asyncio
    async def test_generate_anonymous_no_persist(self, client, cv_request_data):
        app.dependency_overrides[get_current_user_optional] = lambda: None
        try:
            with patch("app.api.v1.cv_endpoint.generate_cv", new_callable=AsyncMock) as mock_gen, \
                 patch("app.api.v1.cv_endpoint.CVRepository.save_cv", new_callable=AsyncMock) as mock_save:
                from app.schemas.cv_response import CVResponse
                mock_gen.return_value = CVResponse(**{
                    "personal": {"nombre_completo": "Anon", "profesion": "Dev", "email": "a@b.com",
                                 "telefono": "1", "linkedin": "l", "rut": "1", "ciudad": "S"},
                    "perfil": {"anios_experiencia": 1, "experticia": "x", "propuesta_valor": "p"},
                    "experiencias": [], "formacion": [], "habilidades": "Python",
                })
                response = await client.post("/api/cv/generate", json=cv_request_data)
        finally:
            app.dependency_overrides.pop(get_current_user_optional, None)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cv_id"] is None
        assert data["persisted"] is False
        assert data["remaining_days"] == 30
        assert "expires_at" in data
        mock_save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_generate_authenticated_persists(self, client, cv_request_data, fake_user):
        mock_save = AsyncMock(return_value="64b000000000000000000000")
        app.dependency_overrides[get_current_user_optional] = _override_auth(fake_user)
        try:
            with patch("app.api.v1.cv_endpoint.generate_cv", new_callable=AsyncMock) as mock_gen, \
                 patch("app.api.v1.cv_endpoint.CVRepository.save_cv", mock_save):
                from app.schemas.cv_response import CVResponse
                mock_gen.return_value = CVResponse(**{
                    "personal": {"nombre_completo": "Auth", "profesion": "Dev", "email": "a@b.com",
                                 "telefono": "1", "linkedin": "l", "rut": "1", "ciudad": "S"},
                    "perfil": {"anios_experiencia": 1, "experticia": "x", "propuesta_valor": "p"},
                    "experiencias": [], "formacion": [], "habilidades": "Python",
                })
                response = await client.post("/api/cv/generate", json=cv_request_data)
        finally:
            app.dependency_overrides.pop(get_current_user_optional, None)

        assert response.status_code == 200
        data = response.json()
        assert data["cv_id"] == "64b000000000000000000000"
        assert data["persisted"] is True
        assert data["user_id"] == "user1"
        mock_save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generate_validation_error(self, client):
        app.dependency_overrides[get_current_user_optional] = lambda: None
        try:
            response = await client.post("/api/cv/generate", json={"user_id": "abc"})
        finally:
            app.dependency_overrides.pop(get_current_user_optional, None)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_quota_exceeded(self, client, cv_request_data):
        app.dependency_overrides[get_current_user_optional] = lambda: None
        try:
            async def raise_quota(_request):
                raise QuotaExceededError("La cuota de la API se ha agotado.")
            with patch("app.api.v1.cv_endpoint.generate_cv", new=raise_quota):
                response = await client.post("/api/cv/generate", json=cv_request_data)
        finally:
            app.dependency_overrides.pop(get_current_user_optional, None)
        assert response.status_code == 429


class TestGetCvEndpoint:
    @pytest.mark.asyncio
    async def test_get_cv_success(self, client, cv_response_data, fake_user):
        cv_with_id = dict(cv_response_data)
        cv_with_id["_id"] = "64b000000000000000000000"
        cv_with_id["user_id"] = "user1"

        app.dependency_overrides[get_current_user] = _override_auth(fake_user)
        try:
            with patch("app.api.v1.cv_endpoint.CVRepository.get_cv_by_id", new=AsyncMock(return_value=cv_with_id)):
                response = await client.get("/api/cv/64b000000000000000000000")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cv_data"]["personal"]["nombre_completo"] == "Jaime Gustamante"
        assert "expires_at" in data["cv_data"]
        assert "remaining_days" in data["cv_data"]

    @pytest.mark.asyncio
    async def test_get_cv_not_found(self, client, fake_user):
        app.dependency_overrides[get_current_user] = _override_auth(fake_user)
        try:
            with patch("app.api.v1.cv_endpoint.CVRepository.get_cv_by_id", new=AsyncMock(return_value=None)):
                response = await client.get("/api/cv/64b000000000000000000000")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_cv_other_user_403(self, client, cv_response_data, fake_user):
        """Un CV de otro usuario no debe ser accesible (anti-IDOR)."""
        cv_with_id = dict(cv_response_data)
        cv_with_id["_id"] = "64b000000000000000000000"
        cv_with_id["user_id"] = "otro-usuario"

        app.dependency_overrides[get_current_user] = _override_auth(fake_user)
        try:
            with patch("app.api.v1.cv_endpoint.CVRepository.get_cv_by_id", new=AsyncMock(return_value=cv_with_id)):
                response = await client.get("/api/cv/64b000000000000000000000")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_expired_cv_returns_404_and_deletes(self, client, cv_response_data, fake_user):
        from datetime import timedelta
        from app.core.datetime_utils import utcnow

        expired_cv = dict(cv_response_data)
        expired_cv["_id"] = "64b000000000000000000000"
        expired_cv["user_id"] = "user1"
        expired_cv["created_at"] = utcnow() - timedelta(days=999)

        app.dependency_overrides[get_current_user] = _override_auth(fake_user)
        try:
            delete_mock = AsyncMock(return_value=True)
            with patch("app.api.v1.cv_endpoint.CVRepository.get_cv_by_id", new=AsyncMock(return_value=expired_cv)), \
                 patch("app.api.v1.cv_endpoint.CVRepository.delete_cv", delete_mock):
                response = await client.get("/api/cv/64b000000000000000000000")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 404
        delete_mock.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_cv_without_auth_401(self, client):
        """Sin token → get_current_user_optional=None → get_current_user lanza 401."""
        app.dependency_overrides[get_current_user_optional] = lambda: None
        try:
            response = await client.get("/api/cv/64b000000000000000000000")
        finally:
            app.dependency_overrides.pop(get_current_user_optional, None)
        assert response.status_code == 401


class TestGetUserCvsEndpoint:
    @pytest.mark.asyncio
    async def test_get_user_cvs(self, client, cv_response_data, fake_user):
        active_cv = dict(cv_response_data)
        active_cv["user_id"] = "user1"

        app.dependency_overrides[get_current_user] = _override_auth(fake_user)
        try:
            with patch("app.api.v1.cv_endpoint.CVRepository.get_cvs_by_user", new=AsyncMock(return_value=[active_cv])):
                response = await client.get("/api/cv/user/user1")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "expires_at" in data["cvs"][0]

    @pytest.mark.asyncio
    async def test_expired_cvs_filtered_out(self, client, cv_response_data, fake_user):
        from datetime import timedelta
        from app.core.datetime_utils import utcnow

        active_cv = dict(cv_response_data)
        active_cv["_id"] = "64b000000000000000000000"
        active_cv["user_id"] = "user1"

        expired_cv = dict(cv_response_data)
        expired_cv["_id"] = "64b000000000000000000001"
        expired_cv["user_id"] = "user1"
        expired_cv["created_at"] = utcnow() - timedelta(days=999)

        app.dependency_overrides[get_current_user] = _override_auth(fake_user)
        try:
            delete_mock = AsyncMock(return_value=True)
            with patch("app.api.v1.cv_endpoint.CVRepository.get_cvs_by_user",
                       new=AsyncMock(return_value=[active_cv, expired_cv])), \
                 patch("app.api.v1.cv_endpoint.CVRepository.delete_cv", delete_mock):
                response = await client.get("/api/cv/user/user1")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        delete_mock.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_other_user_cvs_403(self, client, fake_user):
        app.dependency_overrides[get_current_user] = _override_auth(fake_user)
        try:
            response = await client.get("/api/cv/user/otro-usuario")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_user_cvs_without_auth_401(self, client):
        app.dependency_overrides[get_current_user_optional] = lambda: None
        try:
            response = await client.get("/api/cv/user/user1")
        finally:
            app.dependency_overrides.pop(get_current_user_optional, None)
        assert response.status_code == 401
