"""Tests para app/api/v1/cv_endpoint.py: generación y consulta de CVs."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.llm_service import QuotaExceededError


@pytest_asyncio.fixture
async def client(mongo_connection):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestGenerateCvEndpoint:
    @pytest.mark.asyncio
    async def test_generate_success(self, client, cv_request_data, cv_response):
        with patch(
            "app.services.llm_service.generate_cv",
            new=AsyncMock(return_value=cv_response),
        ):
            with patch(
                "app.api.v1.cv_endpoint.CVRepository.save_cv",
                new=AsyncMock(return_value="64b000000000000000000000"),
            ):
                response = await client.post("/api/cv/generate", json=cv_request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cv_id"] == "64b000000000000000000000"
        assert data["cv_data"]["personal"]["nombre_completo"] == "Jaime Gustamante"
        assert data["remaining_days"] == 30
        assert "expires_at" in data
        assert "remaining_seconds" in data

    @pytest.mark.asyncio
    async def test_generate_validation_error(self, client):
        invalid_data = {"user_id": "abc"}  # faltan todos los demás campos
        response = await client.post("/api/cv/generate", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_quota_exceeded(self, client, cv_request_data):
        async def raise_quota(_request):
            raise QuotaExceededError("La cuota de la API se ha agotado.")

        with patch("app.services.llm_service.generate_cv", new=raise_quota):
            response = await client.post("/api/cv/generate", json=cv_request_data)

        assert response.status_code == 429
        assert "cuota" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_timeout(self, client, cv_request_data):
        async def raise_timeout(_request):
            raise TimeoutError("La IA está tardando demasiado.")

        with patch("app.services.llm_service.generate_cv", new=raise_timeout):
            response = await client.post("/api/cv/generate", json=cv_request_data)

        assert response.status_code == 504

    @pytest.mark.asyncio
    async def test_generate_generic_error(self, client, cv_request_data):
        async def raise_error(_request):
            raise RuntimeError("Falla en el servicio de IA: detalle técnico")

        with patch("app.services.llm_service.generate_cv", new=raise_error):
            response = await client.post("/api/cv/generate", json=cv_request_data)

        assert response.status_code == 500


class TestGetCvEndpoint:
    @pytest.mark.asyncio
    async def test_get_cv_by_id_success(self, client, cv_response_data):
        cv_with_id = dict(cv_response_data)
        cv_with_id["_id"] = "64b000000000000000000000"

        with patch(
            "app.api.v1.cv_endpoint.CVRepository.get_cv_by_id",
            new=AsyncMock(return_value=cv_with_id),
        ):
            response = await client.get("/api/cv/64b000000000000000000000")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cv_data"]["personal"]["nombre_completo"] == "Jaime Gustamante"
        assert "expires_at" in data["cv_data"]
        assert "remaining_days" in data["cv_data"]

    @pytest.mark.asyncio
    async def test_get_cv_not_found(self, client):
        with patch(
            "app.api.v1.cv_endpoint.CVRepository.get_cv_by_id",
            new=AsyncMock(return_value=None),
        ):
            response = await client.get("/api/cv/64b000000000000000000000")

        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_expired_cv_returns_404_and_deletes(self, client, cv_response_data):
        from datetime import datetime, timedelta

        expired_cv = dict(cv_response_data)
        expired_cv["_id"] = "64b000000000000000000000"
        expired_cv["created_at"] = datetime.utcnow() - timedelta(days=999)

        delete_mock = AsyncMock(return_value=True)

        with patch(
            "app.api.v1.cv_endpoint.CVRepository.get_cv_by_id",
            new=AsyncMock(return_value=expired_cv),
        ):
            with patch("app.api.v1.cv_endpoint.CVRepository.delete_cv", new=delete_mock):
                response = await client.get("/api/cv/64b000000000000000000000")

        assert response.status_code == 404
        delete_mock.assert_awaited_once()


class TestGetUserCvsEndpoint:
    @pytest.mark.asyncio
    async def test_get_user_cvs(self, client, cv_response_data):
        fake_cvs = [dict(cv_response_data), dict(cv_response_data)]

        with patch(
            "app.api.v1.cv_endpoint.CVRepository.get_cvs_by_user",
            new=AsyncMock(return_value=fake_cvs),
        ):
            response = await client.get("/api/cv/user/507f1f77bcf86cd799439011")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["cvs"]) == 2
        assert "expires_at" in data["cvs"][0]

    @pytest.mark.asyncio
    async def test_expired_cvs_are_filtered_out(self, client, cv_response_data):
        from datetime import datetime, timedelta

        active_cv = dict(cv_response_data)
        active_cv["_id"] = "64b000000000000000000000"

        expired_cv = dict(cv_response_data)
        expired_cv["_id"] = "64b000000000000000000001"
        expired_cv["created_at"] = datetime.utcnow() - timedelta(days=999)

        delete_mock = AsyncMock(return_value=True)

        with patch(
            "app.api.v1.cv_endpoint.CVRepository.get_cvs_by_user",
            new=AsyncMock(return_value=[active_cv, expired_cv]),
        ):
            with patch("app.api.v1.cv_endpoint.CVRepository.delete_cv", new=delete_mock):
                response = await client.get("/api/cv/user/507f1f77bcf86cd799439011")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        delete_mock.assert_awaited_once()
