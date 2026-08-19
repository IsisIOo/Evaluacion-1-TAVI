"""Fixtures compartidos para los tests del backend."""
import os
import sys
from pathlib import Path

# Fijar variables de entorno ANTES de importar app
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/test_cv_db")
os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-testing")


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

import pytest
from app.core.security import create_access_token
from app.db.models import UserDocument
import pytest_asyncio
from datetime import datetime

from app.schemas.cv_request import CVRequest
from app.schemas.cv_response import CVResponse
from app.db.models import UserDocument
from app.db.session import connect_to_mongo, close_mongo_connection


@pytest_asyncio.fixture
async def mongo_connection():
    await connect_to_mongo()
    yield
    await close_mongo_connection()


@pytest.fixture
def fake_user():
    return UserDocument(
        _id="user1",
        email="test@example.com",
        password_hash="$2b$12$fakehash",
        nombre="Test User",
    )


@pytest.fixture
def auth_headers(fake_user):
    token = create_access_token(fake_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def personal_info_data():
    return {
        "nombre_completo": "Jaime Gustamante",
        "profesion": "Desarrollador Backend",
        "email": "jaime@gmail.com",
        "telefono": "+56 9 1234 5678",
        "linkedin": "https://www.linkedin.com/in/jaime",
        "rut": "12.345.678-K",
        "ciudad": "Santiago",
    }


@pytest.fixture
def perfil_info_data():
    return {
        "anios_experiencia": 3,
        "experticia": "Desarrollo web y APIs en Python",
        "propuesta_valor": "Profesional con 3 años de experiencia construyendo aplicaciones escalables.",
    }


@pytest.fixture
def experiencia_data():
    return [
        {
            "cargo": "Desarrollador Backend",
            "empresa": "TechCorp",
            "pais": "Chile",
            "periodo": "Enero 2023 - Actualidad",
            "descripcion": "Desarrollo de APIs REST con FastAPI y Python.",
            "logros": "Aumenté la eficiencia del sistema en 30%.",
        }
    ]


@pytest.fixture
def formacion_data():
    return [
        {
            "titulo": "Ingeniería Civil en Informática",
            "institucion": "Universidad de Santiago",
            "periodo": "2018 - 2022",
        }
    ]


@pytest.fixture
def cv_request_data(personal_info_data, perfil_info_data, experiencia_data, formacion_data):
    return {
        "user_id": "507f1f77bcf86cd799439011",
        "personal": personal_info_data,
        "perfil": perfil_info_data,
        "experiencias": experiencia_data,
        "formacion": formacion_data,
        "habilidades": "Python, FastAPI, MongoDB, Inglés B2",
    }


@pytest.fixture
def cv_request(cv_request_data) -> CVRequest:
    return CVRequest(**cv_request_data)


@pytest.fixture
def cv_response_data():
    return {
        "personal": {
            "nombre_completo": "Jaime Gustamante",
            "profesion": "Desarrollador Backend",
            "email": "jaime@gmail.com",
            "telefono": "+56 9 1234 5678",
            "linkedin": "https://www.linkedin.com/in/jaime",
            "rut": "12.345.678-K",
            "ciudad": "Santiago",
        },
        "perfil": {
            "anios_experiencia": 3,
            "experticia": "Desarrollo web y APIs",
            "propuesta_valor": "Profesional orientado a resultados.",
        },
        "experiencias": [
            {
                "cargo": "Desarrollador Backend",
                "empresa": "TechCorp",
                "pais": "Chile",
                "periodo": "Enero 2023 - Actualidad",
                "descripcion": "Desarrollo de APIs REST.",
                "logros": "Optimicé consultas SQL.",
            }
        ],
        "formacion": [
            {
                "titulo": "Ingeniería Civil en Informática",
                "institucion": "USACH",
                "periodo": "2018 - 2022",
            }
        ],
        "habilidades": "Python, FastAPI, MongoDB",
    }


@pytest.fixture
def cv_response(cv_response_data) -> CVResponse:
    return CVResponse(**cv_response_data)


@pytest.fixture
def user_document() -> UserDocument:
    return UserDocument(
        email="test@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4fQYy5K5Hm",
        nombre="Test User",
    )
