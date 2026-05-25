import os
from fastapi import HTTPException, APIRouter
import redis
from app.celery_app import celery
from fastapi import HTTPException
from app.tasks.debug import debug_task
from app.tasks.scrape_recipies import scrape_recipes
from celery import states
from dotenv import load_dotenv
load_dotenv()

router = APIRouter()
r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

@router.get('/test-celery')
def test_celery():
    task = debug_task.delay()
    return {"task_id": task.id}

@router.post("/trigger-scrape")
def trigger_scrape():
    last_key = r.get("last_scrape_task_id")
    if last_key:
        last_task = celery.AsyncResult(last_key)
        if last_task.status in (states.PENDING, states.STARTED):
            raise HTTPException(409, "Scrape task is already running")
    task = scrape_recipes.delay()
    r.set("last_scrape_task_id", task.id)
    return {"task_id": task.id}

@router.get("/recipe-scrape-status/{task_id}")
def recipe_scrape_status(task_id:str):
    task = celery.AsyncResult(task_id)
    return {
        "task_id": task.id,
        "status": task.status,
        "error": str(task.result) if task.failed() else None
    }