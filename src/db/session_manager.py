from contextlib import asynccontextmanager
from typing import AsyncGenerator
from threading import local
from celery.signals import worker_process_init
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.core.config import settings
import time # Import time for timestamps

process_local = local()

@worker_process_init.connect(weak=False)
def init_worker_db_connections(**kwargs):
    """Signal handler to create a new engine for each worker process."""
    print(f"[{time.time()}] DB_INIT: Initializing database engine for worker process...")
    engine = create_async_engine(str(settings.DATABASE_DSN), pool_pre_ping=True)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    process_local.engine = engine
    process_local.session_factory = session_factory
    print(f"[{time.time()}] DB_INIT: Database engine initialized.")

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a transactional scope with detailed logging for debugging."""
    print(f"[{time.time()}] GET_DB_SESSION: Attempting to get session.")
    
    if not hasattr(process_local, "session_factory"):
        print(f"[{time.time()}] GET_DB_SESSION: ERROR! session_factory not found!")
        raise RuntimeError("Database session factory not initialized for this worker process.")
    
    print(f"[{time.time()}] GET_DB_SESSION: Session factory found. Creating session...")
    session: AsyncSession = process_local.session_factory()
    print(f"[{time.time()}] GET_DB_SESSION: Session object created. Entering 'try' block.")
    
    try:
        print(f"[{time.time()}] GET_DB_SESSION: Yielding session to task.")
        yield session
        print(f"[{time.time()}] GET_DB_SESSION: Task finished. Committing session.")
        await session.commit()
        print(f"[{time.time()}] GET_DB_SESSION: Commit successful.")
    except Exception:
        print(f"[{time.time()}] GET_DB_SESSION: Exception in task. Rolling back session.")
        await session.rollback()
        print(f"[{time.time()}] GET_DB_SESSION: Rollback successful.")
        raise
    finally:
        print(f"[{time.time()}] GET_DB_SESSION: Entering 'finally' block. Closing session.")
        await session.close()
        print(f"[{time.time()}] GET_DB_SESSION: Session closed.")