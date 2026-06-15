"""Shared test fixtures: in-memory async DB + authenticated HTTP client."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ENVIRONMENT", "local")

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """An HTTP client wired to a fresh in-memory database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    """A client that has set up an account and carries the bearer token."""
    resp = await client.post(
        "/api/v1/auth/setup",
        json={"username": "owner", "password": "secret123"},
    )
    token = resp.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
