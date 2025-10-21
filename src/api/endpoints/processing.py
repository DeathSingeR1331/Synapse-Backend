import uuid
from typing import Annotated
from fastapi import APIRouter, status, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.job import JobCreate, JobCreated, JobStatus
from src.services.real.db_service import RealDatabaseService
from src.db.session import get_db_session
from src.core.celery_app import celery_app
from src.crud import conversation_crud

router = APIRouter()

# -- REMOVED: The old get_database_service dependency is no longer needed --

@router.post(
    "/process",
    response_model=JobCreated,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a new processing job",
)
async def create_processing_job(
    request: Request,
    job_in: JobCreate,
    # ++ MODIFIED: Get the DB session directly, just like in our auth endpoints ++
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Accepts a job, ensures the conversation exists, creates a job record,
    and dispatches the first task.
    """
    job_id = uuid.uuid4()
    
    # ++ ADDED: Instantiate the service with the direct session ++
    db_service = RealDatabaseService(db)

    # This ensures the conversation record exists before any tasks are run.
    await conversation_crud.conversation.get_or_create(
        db=db,
        user_id=job_in.user_id,
        conversation_id=job_in.conversation_id
    )

    await db_service.create_job(job_id=job_id, job_data=job_in)

    job_dict = job_in.model_dump()
    user_id = str(job_in.user_id)
    conversation_id = str(job_in.conversation_id)

    celery_app.send_task(
        "route_input_task",
        args=[str(job_id), user_id, job_dict, conversation_id],
        queue="cpu_light"
    )

    status_url = str(request.url_for("get_job_status", job_id=job_id))
    return JobCreated(job_id=job_id, status_url=status_url)


@router.get(
    "/jobs/status/{job_id}",
    response_model=JobStatus,
    summary="Get the status of a processing job",
)
async def get_job_status(
    job_id: uuid.UUID,
    # ++ MODIFIED: Get the DB session directly here as well for consistency ++
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Retrieve the current status of a job."""
    db_service = RealDatabaseService(db)
    job = await db_service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found.",
        )
    return job