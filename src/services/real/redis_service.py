import uuid
import json
from typing import Dict, List, Optional, Any
from types import TracebackType
import redis.asyncio as redis
from src.services.interfaces._redis import IRedisService, IRedisLock
from src.schemas.websocket import WSClarificationRequest


class RedisLockWrapper(IRedisLock):
    """Wraps a redis.asyncio.Lock to implement the IRedisLock interface."""

    def __init__(self, lock: redis.lock.Lock):
        self._lock = lock

    async def __aenter__(self) -> "IRedisLock":
        await self._lock.acquire()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional["TracebackType"],
    ) -> None:
        await self._lock.release()


class RealRedisService(IRedisService):
    """
    A real implementation of the Redis service for state management,
    locking, and pub/sub notifications.
    """

    def __init__(self, client: redis.Redis):
        self._client = client
    def get_client(self) -> redis.Redis:
        """Returns the underlying redis.asyncio.Redis client instance."""
        return self._client

    async def set_job_state(self, job_id: uuid.UUID, state_data: dict):
        """Stores the volatile state of a job in a Redis HASH."""
        stringified_data = {k: json.dumps(v) for k, v in state_data.items()}
        key = f"job:{job_id}:state"
        await self._client.hset(key, mapping=stringified_data)

    async def get_job_state(self, job_id: uuid.UUID) -> Optional[dict]:
        """Retrieves the state of a job from Redis."""
        key = f"job:{job_id}:state"
        data = await self._client.hgetall(key)
        if data:
            # Deserialize JSON strings back to original types
            return {k: json.loads(v) for k, v in data.items()}
        return None

    def acquire_job_lock(self, job_id: uuid.UUID, timeout: int = 60) -> IRedisLock:
        """Acquires a distributed lock for a specific job_id."""
        lock_key = f"job:{job_id}:lock"
        lock = self._client.lock(lock_key, timeout=timeout, blocking_timeout=5)
        return RedisLockWrapper(lock)

    async def publish_job_update(self, job_id: uuid.UUID, message: dict):
        """Publishes a job update message to the 'job-updates' channel."""
        channel = "job-updates"
        payload = {"job_id": str(job_id), **message}
        await self._client.publish(channel, json.dumps(payload))

    async def store_clarification_request(
        self, job_id: uuid.UUID, request: WSClarificationRequest
    ):
        """Persists the clarification question being asked to the user."""
        key = f"job:{job_id}:clarification"
        await self._client.set(key, request.model_dump_json(), ex=3600 * 24)

    async def get_clarification_request(
        self, job_id: uuid.UUID
    ) -> Optional[WSClarificationRequest]:
        """Retrieves a pending clarification request."""
        key = f"job:{job_id}:clarification"
        data = await self._client.get(key)
        if data:
            return WSClarificationRequest.model_validate_json(data)
        return None
    async def add_message_to_history(
        self,
        conversation_id: uuid.UUID,
        message: Dict[str, Any],
        window_size: int = 50
    ) -> None:
        """
        Atomically adds a message to the conversation history in Redis
        and trims the list to maintain a fixed-size sliding window.
        """
        history_key = f"history:{conversation_id}"
        message_json = json.dumps(message)
        
        async with self._client.pipeline(transaction=True) as pipe:
            pipe.lpush(history_key, message_json)
            pipe.ltrim(history_key, 0, window_size - 1)
            await pipe.execute()

    async def get_recent_history(
        self,
        conversation_id: uuid.UUID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the N most recent messages from the conversation history in Redis.
        """
        history_key = f"history:{conversation_id}"
        recent_messages_json = await self._client.lrange(history_key, 0, limit - 1)
        
        messages = []
        for msg_json in recent_messages_json:
            try:
                # ❌ BUG: msg_json is already a string, .decode() is incorrect.
                # msg = json.loads(msg_json.decode('utf-8'))
                
                # ✅ FIX: Load the string directly.
                msg = json.loads(msg_json)
                messages.append(msg)
            except (json.JSONDecodeError, TypeError):
                # This is good practice in case of corrupted data
                continue
        
        # Reverse the list so it's in chronological order (oldest to newest)
        return messages[::-1]