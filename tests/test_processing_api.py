import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_processing_job_dispatches_task(client: AsyncClient, mocker):
    mock_send_task = mocker.patch(
        "src.api.endpoints.processing.celery_app.send_task"
    )
    test_payload = {
        "user_id": str(uuid.uuid4()),
        "conversation_id": str(uuid.uuid4()),
        "input_type": "text", 
        "input_data": "Hello, world!"
    }
    
    response = await client.post("/api/v1/process", json=test_payload)

    assert response.status_code == 202
    response_json = response.json()
    assert "job_id" in response_json
    assert "status_url" in response_json
    mock_send_task.assert_called_once()
