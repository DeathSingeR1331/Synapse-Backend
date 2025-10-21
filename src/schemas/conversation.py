import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List

# MODIFIED: Added the 'is_personalization_enabled' field
class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    content: str = Field(..., min_length=1, description="The text content of the message.")
    is_personalization_enabled: bool = True
    chat_mode: str = Field(default="personalization", description="Chat mode: personalization, tools, or both")

class MessagePublic(BaseModel):
    """Public-facing schema for a message."""
    uuid: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationWithMessages(BaseModel):
    """Schema for a conversation including its messages."""
    uuid: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessagePublic] = []

    model_config = ConfigDict(from_attributes=True)

# ADDED: New schema for updating a conversation's title
class ConversationUpdate(BaseModel):
    """Schema for updating a conversation's title."""
    title: str = Field(..., min_length=1, max_length=100, description="The new title for the chat.")