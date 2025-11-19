from celery import Celery
from app.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND


celery_app = Celery(
    "whatsapp_agent",
    broker= CELERY_BROKER_URL,
    backend= CELERY_RESULT_BACKEND,
    include=['app.tasks.reminders']
)


# Config
celery_app.conf.update(
    timezone="UTC", 
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1
)