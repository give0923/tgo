"""
Celery application configuration.
"""

from celery import Celery

from ..config import get_settings

# Get settings
settings = get_settings()

# Create Celery app
celery_app = Celery(
    "rag_service",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.rag_service.tasks.document_processing",
        "src.rag_service.tasks.maintenance",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=["json"],
    result_expires=3600,
    timezone=settings.celery_timezone,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    "src.rag_service.tasks.document_processing.*": {"queue": "document_processing"},
    "src.rag_service.tasks.embedding.*": {"queue": "embedding"},
}

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-failed-tasks": {
        "task": "src.rag_service.tasks.maintenance.cleanup_failed_tasks",
        "schedule": 3600.0,  # Every hour
    },
}
