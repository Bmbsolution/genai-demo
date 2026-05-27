"""Integration tests for AuthService against the test DB + Redis + test keys."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from servicecat.errors import AuthenticationError
from servicecat.models import User
from servicecat.services.auth_service import AuthService
from servicecat.services.security import TokenType, decode_token, hash_password

if TYPE_CHECKING:
    import uuid

    from redis.asyncio import Redis
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

EMAIL = "alice@example.com"
PASSWORD = "s3cret-passw0rd"


async def _create_user(
    sm: async_sessionmaker[AsyncSession],
    *,
    email: str = EMAIL,
    password: str = PASSWORD,
    active: bool = True,
) -> uuid.UUID:
    async with sm() as session, session.begin():
        user = User(
            email=email,
            full_name="Alice",
            hashed_password=hash_password(password),
            is_active=active,
        )
        session.add(user)
        await session.flush()
        return user.id


def _service(session: AsyncSession, redis: Redis, keypair: tuple[str, str]) -> AuthService:
    private_pem, public_pem = keypair
    return AuthService(db=session, redis=redis, private_key=private_pem, public_key=public_pem)


async def test_login_success_issues_decodable_tokens(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    jwt_keypair: tuple[str, str],
) -> None:
    user_id = await _create_user(rls_sessionmaker)
    _, public_pem = jwt_keypair
    async with rls_sessionmaker() as session:
        pair = await _service(session, redis_client, jwt_keypair).login(EMAIL, PASSWORD)
    access = decode_token(pair.access_token, public_key=public_pem, expected_type=TokenType.ACCESS)
    refresh = decode_token(
        pair.refresh_token, public_key=public_pem, expected_type=TokenType.REFRESH
    )
    assert access.subject == user_id
    assert refresh.subject == user_id


async def test_login_wrong_password_rejected(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    jwt_keypair: tuple[str, str],
) -> None:
    await _create_user(rls_sessionmaker)
    async with rls_sessionmaker() as session:
        with pytest.raises(AuthenticationError):
            await _service(session, redis_client, jwt_keypair).login(EMAIL, "wrong")


async def test_login_unknown_email_rejected(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    jwt_keypair: tuple[str, str],
) -> None:
    async with rls_sessionmaker() as session:
        with pytest.raises(AuthenticationError):
            await _service(session, redis_client, jwt_keypair).login("nobody@example.com", PASSWORD)


async def test_login_inactive_user_rejected(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    jwt_keypair: tuple[str, str],
) -> None:
    await _create_user(rls_sessionmaker, email="bob@example.com", active=False)
    async with rls_sessionmaker() as session:
        with pytest.raises(AuthenticationError):
            await _service(session, redis_client, jwt_keypair).login("bob@example.com", PASSWORD)


async def test_refresh_rotates_and_revokes_old(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    jwt_keypair: tuple[str, str],
) -> None:
    await _create_user(rls_sessionmaker)
    async with rls_sessionmaker() as session:
        service = _service(session, redis_client, jwt_keypair)
        pair = await service.login(EMAIL, PASSWORD)
        rotated = await service.refresh(pair.refresh_token)
        assert rotated.refresh_token != pair.refresh_token
        with pytest.raises(AuthenticationError, match="revoked"):
            await service.refresh(pair.refresh_token)


async def test_logout_revokes_refresh(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
    redis_client: Redis,
    jwt_keypair: tuple[str, str],
) -> None:
    await _create_user(rls_sessionmaker)
    async with rls_sessionmaker() as session:
        service = _service(session, redis_client, jwt_keypair)
        pair = await service.login(EMAIL, PASSWORD)
        await service.logout(pair.refresh_token)
        with pytest.raises(AuthenticationError, match="revoked"):
            await service.refresh(pair.refresh_token)
