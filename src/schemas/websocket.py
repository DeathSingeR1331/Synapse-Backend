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

# 🔹 ADDED: Schema for the user's answer coming from the frontend.
class WSClarificationResponse(BaseModel):
    """
    Sent FROM the user TO the backend with their selected answer.
    """
    job_id: uuid.UUID
    selected_option: str # The user's chosen option