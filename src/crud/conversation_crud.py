# FILE: src/crud/conversation_crud.py

import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.crud.base import CRUDBase
from src.db.models import Conversation
from src.schemas.user import UserCreate  # Placeholder for CRUDBase generic type

class CRUDConversation(CRUDBase[Conversation, UserCreate, UserCreate]):
    async def get_or_create(
        self, 
        db: AsyncSession, 
        *, 
        user_id: uuid.UUID, 
        conversation_id: uuid.UUID
    ) -> Conversation:
        """
        Tries to get a conversation by its ID for a specific user. 
        If it doesn't exist, it creates a new one with a temporary title.
        """
        # Improved query: Filters by both conversation and user ID for security.
        stmt = select(self.model).where(
            self.model.uuid == conversation_id,
            self.model.user_id == user_id
        )
        result = await db.execute(stmt)
        instance = result.scalars().first()
        
        if instance:
            return instance
        
        # If it doesn't exist, create it with a simple, temporary default title.
        new_conversation = Conversation(
            uuid=conversation_id,
            user_id=user_id,
            title="New Chat"  # This is the temporary title the user sees.
        )
        db.add(new_conversation)
        # flush() sends the change to the DB to get an ID without ending the transaction.
        await db.flush() 
        await db.refresh(new_conversation)
        return new_conversation

# This line makes the class methods available for import elsewhere.
conversation = CRUDConversation(Conversation)