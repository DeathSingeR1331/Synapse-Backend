import redis.asyncio as redis
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from src.core.config import settings

# The connection pool is the shared resource for efficiency.
redis_pool = redis.ConnectionPool.from_url(
    str(settings.REDIS_URL),
    max_connections=20,
    decode_responses=True
)

@asynccontextmanager
async def get_redis_context() -> AsyncGenerator[redis.Redis, None]:
    """
    Provides a Redis client from the pool within a context manager.
    Ideal for use inside async Celery tasks to ensure proper cleanup.
    """
    client = redis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        # For pooled connections, aclose() releases the connection back to the pool.
        await client.aclose()

# This instance is for non-task scopes, like FastAPI dependencies or startup events.
# Re-adding this line fixes the `ImportError`.
redis_client = redis.Redis(connection_pool=redis_pool)