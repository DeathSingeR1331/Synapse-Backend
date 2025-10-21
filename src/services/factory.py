# In Synapse-Worker/src/services/factory.py

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Import the REAL service and the settings
# NOTE: The worker needs to import from the backend's service/config paths.
# This assumes your Dockerfile setup makes the backend code available.
from src.services.real.db_service import RealDatabaseService
from src.core.config import settings

@asynccontextmanager
async def db_service_provider():
    """
    A context manager that provides a database service to a Celery task.
    
    This robust pattern creates a new engine and session for each task,
    ensuring that all async resources are managed within the same event loop
    created by `asyncio.run()`.
    """
    # 1. Create a new engine specifically for this task's event loop.
    engine = create_async_engine(str(settings.DATABASE_DSN), pool_pre_ping=True)
    
    # 2. Create a session factory bound to this new engine.
    AsyncSessionFactory = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    
    async with AsyncSessionFactory() as session:
        try:
            # 3. Yield the service with the new session.
            yield RealDatabaseService(session)
        finally:
            # 4. Cleanly dispose of the engine, which closes all its connections.
            # This runs inside the `async with` block, while the loop is still active.
            await engine.dispose()

# You can create similar providers for other services if needed.