"""
Tests unitarios de los endpoints de CVs: tiempo restante enviado al frontend
y eliminación de CVs vencidos por política de retención.
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.cv_endpoint import get_cv_endpoint, get_user_cvs_endpoint
from app.core.datetime_utils import utcnow

RETENTION_DAYS = 30


def _cv_document(cv_id: str, created_at: datetime) -> dict:
    return {
        "_id": cv_id,
        "user_id": "user1",
        "personal": {"nombre_completo": "Juan Pérez"},
        "created_at": created_at,
    }


class TestGetCvEndpoint:
    @patch("app.api.v1.cv_endpoint.CVRepository.delete_cv", new_callable=AsyncMock)
    @patch("app.api.v1.cv_endpoint.CVRepository.get_cv_by_id", new_callable=AsyncMock)
    async def test_devuelve_tiempo_restante_al_frontend(self, mock_get, mock_delete):
        cv = _cv_document("abc", utcnow() - timedelta(days=10))
        mock_get.return_value = cv

        respuesta = await get_cv_endpoint("abc")

        assert respuesta["success"] is True
        cv_data = respuesta["cv_data"]
        assert cv_data["remaining_days"] == RETENTION_DAYS - 10
        assert cv_data["remaining_seconds"] > 0
        assert cv_data["is_expired"] is False
        assert cv_data["expires_at"].endswith("Z")
        mock_delete.assert_not_awaited()

    @patch("app.api.v1.cv_endpoint.CVRepository.delete_cv", new_callable=AsyncMock)
    @patch("app.api.v1.cv_endpoint.CVRepository.get_cv_by_id", new_callable=AsyncMock)
    async def test_cv_vencido_responde_404_y_se_elimina(self, mock_get, mock_delete):
        cv = _cv_document("abc", utcnow() - timedelta(days=RETENTION_DAYS + 5))
        mock_get.return_value = cv

        with pytest.raises(HTTPException) as excinfo:
            await get_cv_endpoint("abc")

        assert excinfo.value.status_code == 404
        mock_delete.assert_awaited_once_with("abc")

    @patch("app.api.v1.cv_endpoint.CVRepository.get_cv_by_id", new_callable=AsyncMock)
    async def test_cv_inexistente_responde_404(self, mock_get):
        mock_get.return_value = None

        with pytest.raises(HTTPException) as excinfo:
            await get_cv_endpoint("no-existe")

        assert excinfo.value.status_code == 404


class TestGetUserCvsEndpoint:
    @patch("app.api.v1.cv_endpoint.CVRepository.delete_cv", new_callable=AsyncMock)
    @patch("app.api.v1.cv_endpoint.CVRepository.get_cvs_by_user", new_callable=AsyncMock)
    async def test_filtra_y_elimina_cvs_vencidos(self, mock_get_user, mock_delete):
        ahora = utcnow()
        vigente = _cv_document("vigente", ahora - timedelta(days=5))
        vencido = _cv_document("vencido", ahora - timedelta(days=RETENTION_DAYS + 10))
        mock_get_user.return_value = [vigente, vencido]

        respuesta = await get_user_cvs_endpoint("user1")

        assert respuesta["total"] == 1
        assert [cv["_id"] for cv in respuesta["cvs"]] == ["vigente"]
        assert respuesta["cvs"][0]["remaining_days"] == RETENTION_DAYS - 5
        mock_delete.assert_awaited_once_with("vencido")

    @patch("app.api.v1.cv_endpoint.CVRepository.get_cvs_by_user", new_callable=AsyncMock)
    async def test_usuario_sin_cvs_devuelve_lista_vacia(self, mock_get_user):
        mock_get_user.return_value = []

        respuesta = await get_user_cvs_endpoint("user1")

        assert respuesta["total"] == 0
        assert respuesta["cvs"] == []
