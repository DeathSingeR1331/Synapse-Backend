# FILE: src/api/endpoints/websockets.py

import uuid
import json
from typing import Annotated

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
import structlog

from src.websockets.manager import connection_manager
from src.core.config import settings
from src.db.database import get_db_session
from src.services.user_service import UserService
from src.schemas.websocket import WSClarificationResponse
from src.core.celery_app import celery_app
from src.schemas.user import UserPublic

router = APIRouter()
log = structlog.get_logger(__name__)


async def get_current_user_from_token(
    token: Annotated[str | None, Query()] = None,
    db: AsyncSession = Depends(get_db_session),
    user_service: UserService = Depends()
) -> UserPublic | None:
    if token is None:
        log.warn("WebSocket connection attempt without token.")
        return None
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_uuid_str: str | None = payload.get("sub")
        if user_uuid_str is None:
            log.warn("WebSocket auth failed: 'sub' claim missing in token.", payload=payload)
            return None

        user = await user_service.get_user_by_uuid(id=uuid.UUID(user_uuid_str), db=db)
        if user is None or not user.is_active:
            log.warn("WebSocket auth failed: User not found or inactive.", user_uuid=user_uuid_str)
            return None
        
        return user
    except JWTError as e:
        log.error("WebSocket auth failed: JWT decoding error.", exc_info=e)
        return None
    except Exception as e:
        log.error("WebSocket auth failed: An unexpected error occurred.", exc_info=e)
        return None


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    user: Annotated[UserPublic | None, Depends(get_current_user_from_token)]
):
    if not user or str(user.uuid) != client_id:
        log.warn(
            "DETECTIVE LOG: WebSocket connection REJECTED.",
            reason="Policy Violation",
            auth_user_uuid=str(user.uuid) if user else "None",
            requested_client_id=client_id,
        )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await connection_manager.connect(client_id, websocket)
    log.info("DETECTIVE LOG: WebSocket connection ACCEPTED and ACTIVE.", client_id=client_id, user_email=user.email)
    
    try:
        while True:
            raw_data = await websocket.receive_text()
            log.info("DETECTIVE LOG: Received raw text from client.", client_id=client_id, data=raw_data)
            
            try:
                data = json.loads(raw_data)
                log.info("DETECTIVE LOG: Successfully parsed JSON from client.", client_id=client_id, parsed_data=data)
            except json.JSONDecodeError:
                log.error("DETECTIVE LOG: Failed to parse JSON from client.", client_id=client_id, raw_data=raw_data)
                continue

            if data.get("type") == "clarification_response":
                job_id = data.get("job_id")
                response_text = data.get("response")
                
                log.info(f"DETECTIVE LOG: Received clarification for job_id={job_id} with response='{response_text}'")
                
                if job_id and response_text and user and user.uuid:
                    # ✅ FIX: Explicitly define the correct queue for the task.
                    queue_name = "cpu_light"
                    log.info(f"DETECTIVE LOG: Queuing task 'resume_with_clarification_task' to queue='{queue_name}'.", job_id=job_id)
                    
                    celery_app.send_task(
                        "resume_with_clarification_task",
                        args=[job_id, str(user.uuid), response_text],
                        queue=queue_name  # This ensures the task is sent to a worker that is listening.
                    )
                else:
                    log.error(f"DETECTIVE LOG: Missing data for clarification. job_id={job_id}, response={response_text}, user_id={user.uuid}")
            else:
                log.warning(f"DETECTIVE LOG: Received unknown message type: {data.get('type')}. Ignoring.", client_id=client_id)

    except WebSocketDisconnect as e:
        log.warn(
            "DETECTIVE LOG: WebSocket client disconnected.",
            client_id=client_id,
            code=e.code,
            reason=e.reason
        )
        connection_manager.disconnect(client_id)
    except Exception as e:
        log.error(
            "DETECTIVE LOG: An unexpected error occurred in the WebSocket connection.",
            client_id=client_id,
            error=str(e),
            exc_info=True
        )
        connection_manager.disconnect(client_id)