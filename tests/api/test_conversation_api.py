import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User, Conversation
from src.main import app
from src.core.dependencies import get_current_active_user


@pytest.mark.asyncio
async def test_post_message_and_trigger_summarization(
    client: AsyncClient, 
    db_session: AsyncSession, 
    mocker
):
    # ARRANGE
    test_user = User(username="testuser", email="test@test.com", hashed_password="xyz")
    test_convo = Conversation(user=test_user, title="Test Convo")
    db_session.add_all([test_user, test_convo])
    await db_session.flush()

    convo_uuid = test_convo.uuid
    user_uuid = test_user.uuid
    await db_session.commit()

    # Override authentication
    async def override_get_current_user() -> User:
        return test_user
    app.dependency_overrides[get_current_active_user] = override_get_current_user

    mock_send_task = mocker.patch("src.api.endpoints.conversation.celery_app.send_task")

    # ACT & ASSERT
    for i in range(9):
        response = await client.post(
            f"/api/v1/conversations/{convo_uuid}/messages",
            json={"content": f"This is message {i+1}"}
        )
        assert response.status_code == 201
    mock_send_task.assert_not_called()

    response = await client.post(
        f"/api/v1/conversations/{convo_uuid}/messages",
        json={"content": "This is the tenth message!"}
    )
    assert response.status_code == 201

    mock_send_task.assert_called_once_with(
        "summarize_conversation_task",
        args=[str(convo_uuid), str(user_uuid)],
        queue="cpu_heavy",
    )

    del app.dependency_overrides[get_current_active_user]
