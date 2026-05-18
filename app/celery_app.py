from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()

celery = Celery(
    "app",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL"),
    include=["app.tasks.debug", 'app.tasks.scrape_recipies'],
)