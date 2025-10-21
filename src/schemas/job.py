"""
Pydantic schemas for job processing operations.

This module defines the data structures for:
- Creating a new job (JobCreate).
- The response after a job is created (JobCreated).
- The possible states a job can be in (JobStateEnum).
- The detailed status of an existing job (JobStatus).
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class JobStateEnum(str, Enum):
    """Enumeration for the possible states of a processing job."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    # 🔹 ADDED: New state for when the AI is waiting for user input.
    AWAITING_CLARIFICATION = "AWAITING_CLARIFICATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobCreate(BaseModel):
    """Schema for creating a new job."""
    user_id: uuid.UUID = Field(
        ...,
        description="The UUID of the user submitting the job.",
        example="f0fe7c3b-5618-424b-ba75-23f1af5fdee9"
    )
    # Add the new field for personalization
    conversation_id: uuid.UUID = Field(
        ...,
        description="The UUID for the ongoing conversation thread.",
        example="a1b2c3d4-5678-90ab-cdef-1234567890ab"
    )
    input_type: str = Field(
        ...,
        description="The type of input data (e.g., 'text', 'image', 'audio').",
        example="text"
    )
    input_data: Any = Field(
        ...,
        description="The actual data to be processed.",
        example="This is the text to process."
    )


class JobCreated(BaseModel):
    """Schema for the response after a job has been successfully created."""
    job_id: uuid.UUID = Field(..., description="The unique identifier for the created job.")
    status_url: str = Field(..., description="The URL to poll for the job's status.")


class JobStatus(BaseModel):
    """Schema for representing the current status and result of a job."""
    id: uuid.UUID = Field(..., description="The unique identifier of the job.")
    status: JobStateEnum = Field(..., description="The current processing state of the job.")
    created_at: datetime = Field(..., description="The timestamp when the job was created.")
    updated_at: datetime = Field(..., description="The timestamp when the job was last updated.")
    history: List[str] = Field([], description="A log of events for the job's lifecycle.")
    result: Optional[Any] = Field(None, description="The output result of the job upon completion.")

    class Config:
        from_attributes = True