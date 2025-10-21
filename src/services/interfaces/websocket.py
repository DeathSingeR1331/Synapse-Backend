# Synapse-Backend/src/schemas/websocket.py

import uuid
from pydantic import BaseModel
from typing import List

class WSClarificationRequest(BaseModel):
    """
    Schema for a message sent from the backend to the frontend
    when the system needs user input to proceed.
    """
    job_id: uuid.UUID
    query_text: str
    options: List[str]