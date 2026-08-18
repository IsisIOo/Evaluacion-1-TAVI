"""Tests del endpoint POST /generate con autenticación."""
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.dependencies import get_current_user_optional
from app.db.models import UserDocument
from app.schemas.cv_response import CVResponse


def _cv_response():
    return CVResponse(
        personal={"nombre_completo": "Fake", "profesion": "Dev", "email": "f@f.com",
                  "telefono": "1", "linkedin": "l", "rut": "1", "ciudad": "S"},
        perfil={"anios_experiencia": 1, "experticia": "x", "propuesta_valor": "p"},
        experiencias=[], formacion=[], habilidades="Python",
    )


def _request_data():
    return {
        "user_id": "anon-user",
        "personal": {"nombre_completo": "Fake", "profesion": "Dev", "email": "f@f.com",
                     "telefono": "1", "linkedin": "l", "rut": "1", "ciudad": "S"},
        "perfil": {"anios_experiencia": 1, "experticia": "x", "propuesta_valor": "p"},
        "experiencias": [], "formacion": [], "habilidades": "Python",
    }


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestGenerateEndpoint:
    @patch("app.api.v1.cv_endpoint.generate_cv", new_callable=AsyncMock)
    @patch("app.api.v1.cv_endpoint.CVRepository.save_cv", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_anonymous_no_persist(self, mock_save, mock_gen, client):
        mock_gen.return_value = _cv_response()
        app.dependency_overrides[get_current_user_optional] = lambda: None
        try:
            response = await client.post("/api/cv/generate", json=_request_data())
        finally:
            app.dependency_overrides.pop(get_current_user_optional, None)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cv_id"] is None
        assert data["persisted"] is False
        mock_save.assert_not_awaited()

    @patch("app.api.v1.cv_endpoint.generate_cv", new_callable=AsyncMock)
    @patch("app.api.v1.cv_endpoint.CVRepository.save_cv", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_authenticated_persists(self, mock_save, mock_gen, client, fake_user):
        mock_gen.return_value = _cv_response()
        mock_save.return_value = "cv-123"
        app.dependency_overrides[get_current_user_optional] = lambda: fake_user
        try:
            response = await client.post("/api/cv/generate", json=_request_data())
        finally:
            app.dependency_overrides.pop(get_current_user_optional, None)

        assert response.status_code == 200
        data = response.json()
        assert data["cv_id"] == "cv-123"
        assert data["persisted"] is True
        assert data["user_id"] == "user1"
        mock_save.assert_awaited_once()

    @patch("app.api.v1.cv_endpoint.generate_cv", new_callable=AsyncMock)
    @patch("app.api.v1.cv_endpoint.CVRepository.save_cv", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_response_includes_retention(self, mock_save, mock_gen, client):
        mock_gen.return_value = _cv_response()
        app.dependency_overrides[get_current_user_optional] = lambda: None
        try:
            response = await client.post("/api/cv/generate", json=_request_data())
        finally:
            app.dependency_overrides.pop(get_current_user_optional, None)

        data = response.json()
        assert data["expires_at"].endswith("Z")
        assert data["remaining_seconds"] == 30 * 86400
        assert data["remaining_days"] == 30
