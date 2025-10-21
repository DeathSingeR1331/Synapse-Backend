import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.real.db_service import RealDatabaseService
from src.db.models import User, Conversation

@pytest.mark.asyncio
async def test_add_chat_message(db_session: AsyncSession):
    """
    Tests that add_chat_message correctly creates a new row.
    """
    # ARRANGE: Create a user and conversation to link the message to
    test_user = User(username="testuser", email="test@test.com", hashed_password="xyz")
    test_convo = Conversation(user=test_user, title="Test Convo")
    db_session.add_all([test_user, test_convo])
    await db_session.commit()

    db_service = RealDatabaseService(db_session)
    
    # ACT: Call the method we want to test
    new_message = await db_service.add_chat_message(
        user_id=test_user.uuid,
        conversation_id=test_convo.uuid,
        role="user",
        content="Hello, world!"
    )

    # ASSERT: Check that the message was created correctly
    assert new_message.uuid is not None
    assert new_message.role == "user"
    assert new_message.content == "Hello, world!"
    assert new_message.user_id == test_user.uuid