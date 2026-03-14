import os

from app.core.config import settings


def enqueue_task(task, *args) -> str | None:
    """Queue a Celery task and gracefully fall back when broker is unavailable."""
    if settings.database_url.startswith("sqlite"):
        return None
    if os.getenv("DISABLE_CELERY", "").lower() in {"1", "true", "yes"}:
        return None
    try:
        return task.apply_async(args=args, ignore_result=True, retry=False).id
    except Exception:
        return None
