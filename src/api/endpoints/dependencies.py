# Create this file at: Synapse-Backend/src/api/dependencies.py

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

# Import the session factory and service interfaces/implementations
from src.db.session import get_db_session
from src.services.interfaces import IDatabaseService
from src.services.real.db_service import RealDatabaseService
from src.services.mocks.mock_db import MockDatabaseService # For testing
from src.core.config import settings

async def get_database_service(
    session: AsyncSession = Depends(get_db_session)
) -> IDatabaseService:
    """
    Dependency provider that returns the correct database service
    implementation based on the current environment configuration.
    """
    if settings.APP_ENV == "mock":
        return MockDatabaseService()
    return RealDatabaseService(session)