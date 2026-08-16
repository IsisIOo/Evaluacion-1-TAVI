"""Tests para los schemas Pydantic: validación de entrada y salida."""

import pytest
from pydantic import ValidationError

from app.schemas.cv_request import CVRequest, PersonalInfo, PerfilInfo
from app.schemas.cv_response import CVResponse, Personal, Perfil, Experiencia, Formacion
from app.schemas.user import UserCreate, UserResponse


class TestCVRequest:
    def test_valid_request(self, cv_request_data):
        req = CVRequest(**cv_request_data)
        assert req.user_id == cv_request_data["user_id"]
        assert req.personal.nombre_completo == "Jaime Gustamante"
        assert len(req.experiencias) == 1
        assert len(req.formacion) == 1

    def test_missing_user_id_raises(self, cv_request_data):
        cv_request_data.pop("user_id")
        with pytest.raises(ValidationError):
            CVRequest(**cv_request_data)

    def test_missing_personal_raises(self, cv_request_data):
        cv_request_data.pop("personal")
        with pytest.raises(ValidationError):
            CVRequest(**cv_request_data)

    def test_missing_habilidades_raises(self, cv_request_data):
        cv_request_data.pop("habilidades")
        with pytest.raises(ValidationError):
            CVRequest(**cv_request_data)

    def test_empty_experiencias_list_is_valid(self, cv_request_data):
        cv_request_data["experiencias"] = []
        req = CVRequest(**cv_request_data)
        assert req.experiencias == []

    def test_invalid_anios_experiencia_type_raises(self, cv_request_data):
        cv_request_data["perfil"]["anios_experiencia"] = "tres"
        with pytest.raises(ValidationError):
            CVRequest(**cv_request_data)


class TestPersonalInfo:
    def test_valid_personal_info(self, personal_info_data):
        info = PersonalInfo(**personal_info_data)
        assert info.email == "jaime@gmail.com"
        assert info.telefono == "+56 9 1234 5678"


class TestPerfilInfo:
    def test_valid_perfil(self, perfil_info_data):
        perfil = PerfilInfo(**perfil_info_data)
        assert perfil.anios_experiencia == 3
        assert isinstance(perfil.anios_experiencia, int)


class TestCVResponse:
    def test_valid_response(self, cv_response_data):
        resp = CVResponse(**cv_response_data)
        assert resp.personal.nombre_completo == "Jaime Gustamante"
        assert isinstance(resp.experiencias[0], Experiencia)
        assert isinstance(resp.formacion[0], Formacion)
        assert resp.habilidades == "Python, FastAPI, MongoDB"

    def test_missing_personal_raises(self, cv_response_data):
        cv_response_data.pop("personal")
        with pytest.raises(ValidationError):
            CVResponse(**cv_response_data)

    def test_missing_perfil_raises(self, cv_response_data):
        cv_response_data.pop("perfil")
        with pytest.raises(ValidationError):
            CVResponse(**cv_response_data)

    def test_missing_experiencias_raises(self, cv_response_data):
        cv_response_data.pop("experiencias")
        with pytest.raises(ValidationError):
            CVResponse(**cv_response_data)

    def test_missing_formacion_raises(self, cv_response_data):
        cv_response_data.pop("formacion")
        with pytest.raises(ValidationError):
            CVResponse(**cv_response_data)

    def test_missing_habilidades_raises(self, cv_response_data):
        cv_response_data.pop("habilidades")
        with pytest.raises(ValidationError):
            CVResponse(**cv_response_data)

    def test_model_dump_roundtrip(self, cv_response):
        dumped = cv_response.model_dump()
        restored = CVResponse(**dumped)
        assert restored.personal == cv_response.personal

    def test_submodel_validation(self):
        with pytest.raises(ValidationError):
            Personal(nombre_completo="Solo nombre")

        with pytest.raises(ValidationError):
            Perfil(anios_experiencia=1)


class TestUserSchemas:
    def test_valid_user_create(self):
        user = UserCreate(email="test@example.com", password="clave123", nombre="Test")
        assert user.email == "test@example.com"
        assert user.password == "clave123"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(email="no-es-email", password="clave123", nombre="Test")

    def test_short_password_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", password="123", nombre="Test")

    def test_valid_user_response(self):
        user = UserResponse(
            id="507f1f77bcf86cd799439011",
            email="test@example.com",
            nombre="Test",
            is_active=True,
        )
        assert user.id == "507f1f77bcf86cd799439011"
        assert user.is_active is True
