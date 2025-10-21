# Synapse-Backend/src/services/interfaces/_db.py

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional, Any

# We will create these schemas in the next step
from src.schemas.job import JobCreate, JobStatus, JobStateEnum


class IDatabaseService(ABC):
    """Abstract interface for database operations related to jobs."""

    @abstractmethod
    async def create_job(self, job_id: uuid.UUID, job_data: JobCreate) -> JobStatus:
        """Creates a new job record in the database."""
        raise NotImplementedError

    @abstractmethod
    async def get_job_by_id(self, job_id: uuid.UUID) -> Optional:
        """Retrieves a job record by its ID."""
        raise NotImplementedError

    @abstractmethod
    async def update_job_status(
        self, job_id: uuid.UUID, status: JobStateEnum, result: Optional[Any] = None
    ) -> JobStatus:
        """Updates the status and result of an existing job."""
        raise NotImplementedError

    @abstractmethod
    async def add_job_history_event(
        self, job_id: uuid.UUID, event_description: str
    ) -> List[str]:
        """Adds a new entry to the job's history log."""
        raise NotImplementedError