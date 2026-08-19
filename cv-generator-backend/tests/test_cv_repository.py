"""
Tests unitarios del CVRepository en lo referente a retención de datos.
"""
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.config import settings
from app.core.datetime_utils import utcnow
from app.db.cv_repository import CVRepository
from app.schemas.cv_response import CVResponse


def _mock_db(collection=None):
    db = MagicMock()
    db.__getitem__.return_value = collection
    return db


def _sample_cv_response() -> CVResponse:
    return CVResponse(
        personal={
            "nombre_completo": "Juan Pérez",
            "profesion": "Ingeniero",
            "email": "juan@example.com",
            "telefono": "+56 9 1234 5678",
            "linkedin": "https://www.linkedin.com/in/juan",
            "rut": "12.345.678-9",
            "ciudad": "Santiago",
        },
        perfil={
            "anios_experiencia": 5,
            "experticia": "Python",
            "propuesta_valor": "Ingeniero con 5 años de experiencia.",
        },
        experiencias=[
            {
                "cargo": "Backend Dev",
                "empresa": "Empresa S.A.",
                "pais": "Chile",
                "periodo": "2020-2023",
                "descripcion": "Desarrollo backend.",
                "logros": "Aumento de rendimiento.",
            }
        ],
        formacion=[
            {
                "titulo": "Ingeniería",
                "institucion": "U. de Chile",
                "periodo": "2015-2020",
            }
        ],
        habilidades="Python (Avanzado), Inglés (B2)",
    )


class TestSaveCv:
    @patch("app.db.cv_repository.get_db")
    async def test_guardar_cv_incluye_expires_at(self, mock_get_db):
        collection = MagicMock()
        insert_result = MagicMock()
        insert_result.inserted_id = "cv123"
        collection.insert_one = AsyncMock(return_value=insert_result)
        mock_get_db.return_value = _mock_db(collection)

        cv_id = await CVRepository.save_cv(_sample_cv_response(), user_id="user1")

        assert cv_id == "cv123"
        doc_guardado = collection.insert_one.await_args.args[0]
        assert doc_guardado["created_at"] == doc_guardado["updated_at"]
        esperado = doc_guardado["created_at"] + timedelta(days=settings.CV_RETENTION_DAYS)
        assert doc_guardado["expires_at"] == esperado
        assert doc_guardado["user_id"] == "user1"


class TestDeleteExpiredCvs:
    @patch("app.db.cv_repository.get_db")
    async def test_elimina_cvs_vencidos_con_filtro_correcto(self, mock_get_db):
        collection = MagicMock()
        delete_result = MagicMock()
        delete_result.deleted_count = 4
        collection.delete_many = AsyncMock(return_value=delete_result)
        mock_get_db.return_value = _mock_db(collection)

        eliminados = await CVRepository.delete_expired_cvs()

        assert eliminados == 4
        filtro = collection.delete_many.await_args.args[0]
        assert "created_at" in filtro
        assert "$lte" in filtro["created_at"]

        cutoff = filtro["created_at"]["$lte"]
        ahora = utcnow()
        esperado = ahora - timedelta(days=settings.CV_RETENTION_DAYS)
        assert abs((cutoff - esperado).total_seconds()) < 5

    @patch("app.db.cv_repository.get_db")
    async def test_sin_cvs_vencidos_devuelve_cero(self, mock_get_db):
        collection = MagicMock()
        delete_result = MagicMock()
        delete_result.deleted_count = 0
        collection.delete_many = AsyncMock(return_value=delete_result)
        mock_get_db.return_value = _mock_db(collection)

        assert await CVRepository.delete_expired_cvs() == 0


class TestEnsureRetentionIndex:
    @patch("app.db.cv_repository.get_db")
    async def test_crea_indice_ttl_sobre_created_at(self, mock_get_db):
        collection = MagicMock()
        collection.create_index = AsyncMock(return_value="cv_created_at_ttl")
        mock_get_db.return_value = _mock_db(collection)

        nombre = await CVRepository.ensure_retention_index()

        assert nombre == "cv_created_at_ttl"
        llamada = collection.create_index.await_args
        assert llamada.args[0] == "created_at"
        assert llamada.kwargs["expireAfterSeconds"] == settings.CV_RETENTION_DAYS * 86400
        assert llamada.kwargs["name"] == "cv_created_at_ttl"
