"""Tests para app/core/security.py: hashing de contraseñas y JWT."""

import pytest
from jose import jwt

from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_SECRET,
    ALGORITHM,
    get_password_hash,
    verify_password,
    create_access_token,
)


class TestPasswordHash:
    def test_hash_password_returns_hash(self):
        hashed = get_password_hash("mi-password-segura")
        assert isinstance(hashed, str)
        assert hashed != "mi-password-segura"
        assert hashed.startswith("$2b$")

    def test_hash_is_unique(self):
        hash1 = get_password_hash("misma-password")
        hash2 = get_password_hash("misma-password")
        assert hash1 != hash2  # bcrypt usa salt aleatorio

    def test_verify_correct_password(self):
        hashed = get_password_hash("clave123")
        assert verify_password("clave123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = get_password_hash("clave123")
        assert verify_password("clave-incorrecta", hashed) is False


class TestAccessToken:
    def test_create_access_token_returns_jwt(self):
        token = create_access_token(subject="507f1f77bcf86cd799439011")
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        assert decoded["sub"] == "507f1f77bcf86cd799439011"

    def test_token_has_expiration(self):
        token = create_access_token(subject="user-1")
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        assert "exp" in decoded

    def test_token_expires_after_configured_minutes(self):
        token = create_access_token(subject="user-1")
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        import time
        remaining = decoded["exp"] - time.time()
        assert remaining > 0
        assert remaining <= ACCESS_TOKEN_EXPIRE_MINUTES * 60 + 5
