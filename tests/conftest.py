"""
Pytest configuration file for the application.

This file sets up fixtures for managing the test database, providing
transaction-isolated database sessions to tests, and creating an HTTP client
for making API requests to the application.
"""
import asyncio
from typing import AsyncGenerator

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncConnection,
)

from src.main import app
from src.db.database import Base, get_db_session
from src.core.config import settings

# Use a separate database for testing
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_SERVER}/test_{settings.POSTGRES_DB}"
)

# Create an async engine and session maker for the test database
engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

# The custom event_loop fixture is no longer needed with modern pytest-asyncio,
# which now manages the asyncio event loop automatically and correctly.

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """
    Manages the test database schema for the entire test session.
    It creates all tables before any tests run and drops them after all tests complete.
    """
    async with engine.begin() as conn:
        # Drop all tables first to ensure a clean state from any previous failed runs
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a transaction-isolated database session for each test function.

    This fixture creates a new connection and begins a transaction. The session
    is yielded to the test. After the test completes, the transaction is rolled back,
    ensuring that any database changes are undone and each test runs in a clean state.
    """
    connection: AsyncConnection = await engine.connect()
    transaction = await connection.begin()
    
    session = TestingSessionLocal(bind=connection)

    yield session

    # Clean up the session and roll back the transaction
    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Creates an async HTTP client for the FastAPI app, with the database
    dependency overridden to use the isolated test session.
    """

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        """Override dependency to yield the test-specific session."""
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    # Use ASGITransport to test the app directly without a running server
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    # Clean up the dependency override after the test
    del app.dependency_overrides[get_db_session]