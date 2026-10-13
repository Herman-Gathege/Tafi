"""Celery application.

Kept in a single module so the queue technology can be swapped later without
touching the rest of the codebase (Sprint 1 spike T1-13).
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("tafi", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Africa/Nairobi",
    enable_utc=True,
    task_track_started=True,
)


@celery_app.task(name="tafi.noop")
def noop() -> str:
    """Placeholder task: proves the worker starts, connects and consumes."""
    return "ok"
