"""Tests para app/core/security.py y app/core/dependencies.py."""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from jose import jwt
from fastapi import HTTPException

from app.core import security
from app.core.config import settings
from app.core.dependencies import get_current_user, get_current_user_optional
from app.db.models import UserDocument


class TestPasswordHash:
    def test_hash_password_returns_hash(self):
        hashed = security.get_password_hash("mi-password-segura")
        assert isinstance(hashed, str)
        assert hashed != "mi-password-segura"
        assert hashed.startswith("$2b$")

    def test_hash_is_unique(self):
        hash1 = security.get_password_hash("misma-password")
        hash2 = security.get_password_hash("misma-password")
        assert hash1 != hash2

    def test_verify_correct_password(self):
        hashed = security.get_password_hash("clave123")
        assert security.verify_password("clave123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = security.get_password_hash("clave123")
        assert security.verify_password("clave-incorrecta", hashed) is False


class TestAccessToken:
    def test_create_access_token_returns_jwt(self):
        token = security.create_access_token(subject="user-123")
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert decoded["sub"] == "user-123"

    def test_token_has_expiration(self):
        token = security.create_access_token(subject="user-1")
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert "exp" in decoded

    def test_roundtrip(self):
        token = security.create_access_token("user-456")
        assert security.decode_access_token(token) == "user-456"

    def test_decode_with_wrong_secret_returns_none(self):
        token = jwt.encode({"sub": "user-1", "exp": 9999999999}, "wrong-secret", algorithm="HS256")
        assert security.decode_access_token(token) is None

    def test_decode_invalid_token_returns_none(self):
        assert security.decode_access_token("not-a-jwt") is None

    def test_decode_empty_token_returns_none(self):
        assert security.decode_access_token("") is None


class TestAuthDependencies:
    def _credentials(self, token: str) -> SimpleNamespace:
        return SimpleNamespace(credentials=token)

    @patch("app.core.dependencies.UserRepository")
    async def test_optional_returns_user_with_valid_token(self, mock_repo_cls):
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_by_id = AsyncMock(
            return_value=UserDocument(_id="u1", email="a@b.com", password_hash="h", nombre="A")
        )
        token = security.create_access_token("u1")

        result = await get_current_user_optional(
            credentials=self._credentials(token), db=object()
        )

        assert result is not None
        assert result.id == "u1"

    @patch("app.core.dependencies.UserRepository")
    async def test_optional_returns_none_for_inactive_user(self, mock_repo_cls):
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_by_id = AsyncMock(
            return_value=UserDocument(_id="u1", email="a@b.com", password_hash="h", nombre="A", is_active=False)
        )
        token = security.create_access_token("u1")

        result = await get_current_user_optional(
            credentials=self._credentials(token), db=object()
        )

        assert result is None

    async def test_optional_returns_none_without_credentials(self):
        result = await get_current_user_optional(credentials=None, db=object())
        assert result is None

    async def test_optional_returns_none_with_bad_token(self):
        result = await get_current_user_optional(
            credentials=self._credentials("garbage"), db=object()
        )
        assert result is None

    async def test_get_current_user_passes_through(self):
        user = UserDocument(_id="u1", email="a@b.com", password_hash="h", nombre="A")
        assert await get_current_user(user=user) is user

    async def test_get_current_user_raises_401_for_none(self):
        with pytest.raises(HTTPException) as excinfo:
            await get_current_user(user=None)
        assert excinfo.value.status_code == 401
        assert excinfo.value.headers["WWW-Authenticate"] == "Bearer"
