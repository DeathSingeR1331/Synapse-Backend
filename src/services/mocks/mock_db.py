import uuid
import redis
import json
from datetime import datetime, timezone
from src.schemas.job import JobCreate, JobStatus, JobStateEnum
from src.services.interfaces._db import IDatabaseService
from src.core.config import settings

class MockDatabaseService(IDatabaseService):
    """
    A mock implementation of the database service using REDIS as a shared,
    in-memory key-value store. This allows state to be shared across containers.
    """
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        print("MOCK_DB: Connected to Redis.")

    def _get_job_key(self, job_id: uuid.UUID) -> str:
        return f"job:{str(job_id)}"

    # Async methods for backend API usage
    async def create_job(self, job_id: uuid.UUID, job_data: JobCreate) -> JobStatus:
        print(f"MOCK_DB (Redis): Creating job {job_id}...")
        now = datetime.now(timezone.utc)
        new_job = JobStatus(
            id=job_id,
            status=JobStateEnum.PENDING,
            created_at=now,
            updated_at=now,
            history=["Job created"],
        )
        self.redis_client.set(self._get_job_key(job_id), new_job.model_dump_json())
        return new_job

    async def get_job_by_id(self, job_id: uuid.UUID) -> JobStatus | None:
        print(f"MOCK_DB (Redis): Getting job {job_id}...")
        job_json = self.redis_client.get(self._get_job_key(job_id))
        if job_json:
            return JobStatus.model_validate_json(job_json)
        return None

    async def update_job_status(self, job_id: uuid.UUID, status: JobStateEnum) -> JobStatus:
        print(f"MOCK_DB (Redis): Updating job {job_id} to status {status.value}...")
        job = await self.get_job_by_id(job_id)
        if job:
            job.status = status
            job.updated_at = datetime.now(timezone.utc)
            job.history.append(f"Status updated to {status.value}")
            self.redis_client.set(self._get_job_key(job_id), job.model_dump_json())
            return job
        raise ValueError("Job not found in Redis")

    # Synchronous methods for Celery worker usage
    def get_job_by_id_sync(self, job_id: uuid.UUID) -> JobStatus | None:
        print(f"MOCK_DB (Redis): (sync) Getting job {job_id}...")
        job_json = self.redis_client.get(self._get_job_key(job_id))
        if job_json:
            return JobStatus.model_validate_json(job_json)
        return None

    def update_job_status_sync(self, job_id: uuid.UUID, status: JobStateEnum) -> JobStatus:
        print(f"MOCK_DB (Redis): (sync) Updating job {job_id} to status {status.value}...")
        job = self.get_job_by_id_sync(job_id)
        if job:
            job.status = status
            job.updated_at = datetime.now(timezone.utc)
            job.history.append(f"Status updated to {status.value}")
            self.redis_client.set(self._get_job_key(job_id), job.model_dump_json())
            return job
        raise ValueError("Job not found in Redis")
