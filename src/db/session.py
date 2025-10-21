from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.core.config import settings

# Create an asynchronous engine instance
engine = create_async_engine(
    str(settings.DATABASE_DSN),
    pool_pre_ping=True,
    echo=False  # Set to True to log all generated SQL
)

# Create a factory for asynchronous sessions
AsyncSessionFactory = async_sessionmaker(
    engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)

async def get_db_session() -> AsyncSession:
    """
    Dependency that yields a SQLAlchemy async session.
    Ensures the session is properly closed after use.
    """
    async with AsyncSessionFactory() as session:
        yield session
