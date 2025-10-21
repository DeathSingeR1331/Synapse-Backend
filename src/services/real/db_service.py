import uuid
from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.schemas.job import JobCreate, JobStatus, JobStateEnum
from src.db.models import ProcessingJob, User, ChatMessage, ConversationSummary


class RealDatabaseService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_job(self, job_id: uuid.UUID, job_data: JobCreate) -> JobStatus:
        """Creates a new job record in the 'processing_jobs' table."""
        
        new_job = ProcessingJob(
            uuid=job_id,
            user_id=job_data.user_id, 
            job_type=job_data.input_type,
            status=JobStateEnum.PENDING.value,
            input_data=job_data.input_data,
        )
        self._session.add(new_job)
        await self._session.commit()
        await self._session.refresh(new_job)

        return JobStatus(
            id=new_job.uuid,
            status=JobStateEnum(new_job.status),
            created_at=new_job.created_at,
            updated_at=new_job.created_at,
            history=["Job created"],
            result=None,
        )

    async def get_job_by_id(self, job_id: uuid.UUID) -> Optional[JobStatus]:
        """Retrieves a job from the 'processing_jobs' table."""
        job = await self._session.get(ProcessingJob, job_id)
        if not job:
            return None

        last_update_time = job.completed_at or job.started_at or job.created_at

        return JobStatus(
            id=job.uuid,
            status=JobStateEnum(job.status),
            created_at=job.created_at,
            updated_at=last_update_time,
            history=["Job retrieved"],
            result=job.result_data,
        )

    async def update_job_status(
        self, job_id: uuid.UUID, status: JobStateEnum, result: Optional[Any] = None
    ) -> JobStatus:
        """Updates the status of a job in the 'processing_jobs' table."""
        job = await self._session.get(ProcessingJob, job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found in processing_jobs table.")

        job.status = status.value

        if status == JobStateEnum.PROCESSING and not job.started_at:
            job.started_at = func.now()

        if status in [JobStateEnum.COMPLETED, JobStateEnum.FAILED]:
            job.completed_at = func.now()

        if result is not None:
            if status == JobStateEnum.FAILED:
                job.error_message = str(result)
                job.result_data = None
            else:
                job.result_data = result
                job.error_message = None

        self._session.add(job)
        await self._session.commit()
        await self._session.refresh(job)

        last_update_time = job.completed_at or job.started_at or job.created_at

        return JobStatus(
            id=job.uuid,
            status=JobStateEnum(job.status),
            created_at=job.created_at,
            updated_at=last_update_time,
            history=["Job status updated"],
            result=job.result_data,
        )

    async def add_job_history_event(
        self, job_id: uuid.UUID, event_description: str
    ) -> List[str]:
        # This placeholder function is fine as is
        print(f"HISTORY for {job_id}: {event_description}")
        return [event_description]
    
    # --- Methods for Conversational Memory ---
    async def add_chat_message(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        job_id: Optional[uuid.UUID] = None,
        extra_meta: Optional[dict] = None
    ) -> ChatMessage:
        """Creates and saves a new chat message to the database."""
        new_message = ChatMessage(
            user_id=user_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            job_id=job_id,
            extra_meta=extra_meta
        )
        self._session.add(new_message)
        await self._session.commit()
        await self._session.refresh(new_message)
        return new_message

    async def get_conversation_message_count(self, conversation_id: uuid.UUID) -> int:
        """Counts the total number of messages in a given conversation."""
        stmt = select(func.count(ChatMessage.uuid)).where(ChatMessage.conversation_id == conversation_id)
        result = await self._session.execute(stmt)
        count = result.scalars().first()
        return count if count is not None else 0

    async def get_conversation_summary(self, conversation_id: uuid.UUID) -> Optional[str]:
        """
        Retrieves the most recent summary for a given conversation.
        Returns the summary text or None if no summary exists.
        """
        stmt = select(ConversationSummary.summary).where(ConversationSummary.conversation_id == conversation_id)
        result = await self._session.execute(stmt)
        summary = result.scalars().first()
        return summary