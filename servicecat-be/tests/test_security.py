"""Unit tests for password hashing and JWT token handling (no DB/Redis)."""

from __future__ import annotations

import datetime as dt
import uuid

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from servicecat.errors import AuthenticationError
from servicecat.services.security import (
    DecodedToken,
    TokenType,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)


def _generate_keypair() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = (
        key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


@pytest.fixture(scope="module")
def keypair() -> tuple[str, str]:
    return _generate_keypair()


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed) is True
    assert verify_password("wrong password", hashed) is False


def test_verify_password_rejects_malformed_hash() -> None:
    assert verify_password("anything", "not-a-valid-argon2-hash") is False


def test_token_roundtrip(keypair: tuple[str, str]) -> None:
    private_pem, public_pem = keypair
    subject = uuid.uuid4()
    token, jti = create_token(
        subject=subject,
        token_type=TokenType.ACCESS,
        ttl_seconds=900,
        private_key=private_pem,
    )
    decoded = decode_token(token, public_key=public_pem, expected_type=TokenType.ACCESS)
    assert isinstance(decoded, DecodedToken)
    assert decoded.subject == subject
    assert decoded.token_type is TokenType.ACCESS
    assert decoded.jti == jti
    assert decoded.expires_at > dt.datetime.now(dt.UTC)


def test_expired_token_is_rejected(keypair: tuple[str, str]) -> None:
    private_pem, public_pem = keypair
    token, _ = create_token(
        subject=uuid.uuid4(),
        token_type=TokenType.ACCESS,
        ttl_seconds=-1,
        private_key=private_pem,
    )
    with pytest.raises(AuthenticationError, match="expired"):
        decode_token(token, public_key=public_pem)


def test_token_signed_by_other_key_is_rejected(keypair: tuple[str, str]) -> None:
    private_pem, _ = keypair
    _, unrelated_public = _generate_keypair()
    token, _ = create_token(
        subject=uuid.uuid4(),
        token_type=TokenType.ACCESS,
        ttl_seconds=900,
        private_key=private_pem,
    )
    with pytest.raises(AuthenticationError, match="Invalid"):
        decode_token(token, public_key=unrelated_public)


def test_wrong_token_type_is_rejected(keypair: tuple[str, str]) -> None:
    private_pem, public_pem = keypair
    token, _ = create_token(
        subject=uuid.uuid4(),
        token_type=TokenType.ACCESS,
        ttl_seconds=900,
        private_key=private_pem,
    )
    with pytest.raises(AuthenticationError, match="refresh"):
        decode_token(token, public_key=public_pem, expected_type=TokenType.REFRESH)
