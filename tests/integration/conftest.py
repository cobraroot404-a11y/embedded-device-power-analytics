"""Integration test fixtures.

These tests need a real reachable PostgreSQL/TimescaleDB instance (the schema
requires a hypertable + Timescale-specific SQL from the Alembic migration, so
SQLite or an ORM create_all() stand-in would not exercise the real code path).
Point DATABASE_URL at either:
  - `docker compose -p embedded_device_power_analytics up -d timescaledb`
    (matches the Settings default: localhost:5432), or
  - the Postgres/Timescale service container used in CI.
"""

import subprocess
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.db.session import async_session_factory, engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _run_migrations():
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    yield


@pytest_asyncio.fixture(autouse=True)
async def _fresh_engine_per_test():
    """pytest-asyncio gives each test function its own event loop by
    default, but `engine` is a module-level singleton created once at import
    time. Disposing it before every test forces a fresh connection pool bound
    to *this* test's loop, instead of asyncpg connections leaking across
    loops (which raises "attached to a different loop" on the second test)."""
    await engine.dispose()
    yield


@pytest_asyncio.fixture
async def db_session():
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables():
    yield
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE telemetry_events, anomalies, devices CASCADE"))


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
