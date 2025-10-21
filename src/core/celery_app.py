# In: Synapse-Backend/src/core/celery_app.py

from celery import Celery
from src.core.config import settings

# This creates a lightweight client instance for the backend.
# Its only job is to send tasks to Redis.
celery_app = Celery(
    "synapse_client",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
# 👇 ADD THIS CONFIGURATION BLOCK
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)