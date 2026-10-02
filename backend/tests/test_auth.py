"""
Tests for authentication: password hashing and JWT token management.
"""

import pytest
from datetime import timedelta

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Test bcrypt password hashing and verification."""

    def test_hash_and_verify(self):
        password = "SecureP@ssw0rd123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        password = "CorrectPassword"
        hashed = hash_password(password)
        assert verify_password("WrongPassword", hashed) is False

    def test_hash_is_not_plaintext(self):
        password = "MySecret"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 20

    def test_different_hashes_for_same_password(self):
        password = "SamePassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        # bcrypt generates different salts
        assert hash1 != hash2
        # But both should verify
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_and_decode_token(self):
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "123"
        assert decoded["email"] == "test@example.com"

    def test_token_has_expiration(self):
        token = create_access_token({"sub": "1"})
        decoded = decode_access_token(token)
        assert "exp" in decoded

    def test_expired_token_returns_none(self):
        token = create_access_token(
            {"sub": "1"},
            expires_delta=timedelta(seconds=-1),
        )
        decoded = decode_access_token(token)
        assert decoded is None

    def test_invalid_token_returns_none(self):
        decoded = decode_access_token("not.a.valid.token")
        assert decoded is None

    def test_tampered_token_returns_none(self):
        token = create_access_token({"sub": "1"})
        # Tamper with the token
        tampered = token[:-5] + "XXXXX"
        decoded = decode_access_token(tampered)
        assert decoded is None
