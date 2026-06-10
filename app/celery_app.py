from celery import Celery
from app.config import settings
from app.core.logging import setup_logging

setup_logging()

celery = Celery(
    "app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.debug", "app.tasks.scrape_recipies"],
)
