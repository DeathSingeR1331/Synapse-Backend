import uuid
from abc import ABC, abstractmethod
from typing import Optional
from types import TracebackType

# We will create this schema later for the WebSocket communication
from src.schemas.websocket import WSClarificationRequest


class IRedisLock(ABC):
    """Abstract interface for a distributed lock."""

    @abstractmethod
    async def __aenter__(self) -> "IRedisLock":
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        raise NotImplementedError


class IRedisService(ABC):
    """Abstract interface for Redis operations."""

    @abstractmethod
    async def set_job_state(self, job_id: uuid.UUID, state_data: dict) -> None:
        """Stores the volatile state of a job in Redis."""
        raise NotImplementedError

    @abstractmethod
    async def get_job_state(self, job_id: uuid.UUID) -> Optional[dict]:
        """Retrieves the state of a job from Redis."""
        raise NotImplementedError

    @abstractmethod
    def acquire_job_lock(self, job_id: uuid.UUID, timeout: int = 60) -> IRedisLock:
        """Acquires a distributed lock for a specific job_id."""
        raise NotImplementedError

    @abstractmethod
    async def publish_job_update(self, job_id: uuid.UUID, message: dict) -> None:
        """Publishes a job update message to a specific channel."""
        raise NotImplementedError

    @abstractmethod
    async def store_clarification_request(
        self, job_id: uuid.UUID, request: WSClarificationRequest
    ) -> None:
        """Persists a clarification question for a user."""
        raise NotImplementedError

    @abstractmethod
    async def get_clarification_request(
        self, job_id: uuid.UUID
    ) -> Optional[WSClarificationRequest]:
        """Retrieves a pending clarification request."""
        raise NotImplementedError
