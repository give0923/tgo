"""
Celery tasks for async processing.
"""

from .celery_app import celery_app
from .document_processing import process_file_task

__all__ = [
    "celery_app",
    "process_file_task",
]
