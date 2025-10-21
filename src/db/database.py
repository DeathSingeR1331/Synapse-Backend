from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from src.core.config import settings

# Use the DSN from your settings for the engine
engine = create_async_engine(str(settings.DATABASE_DSN), pool_pre_ping=True)

# Create a factory for asynchronous sessions
AsyncSessionFactory = async_sessionmaker(
    engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)

# Base class for all your SQLAlchemy models to inherit from
Base = declarative_base()

async def get_db_session() -> AsyncSession:
    """
    FastAPI dependency that yields a SQLAlchemy async session.
    Ensures the session is properly closed after use.
    """
    async with AsyncSessionFactory() as session:
        yield session