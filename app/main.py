from app.celery_app import celery
from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select
from app.api.schemas import RecipeResponse, RecipeWithIngredientsResponse
from app.tasks.debug import debug_task
from app.db.engine import get_session
from app.models.Recipe import Recipe
from app.tasks.scrape_recipies import scrape_recipes
import redis
import os
from dotenv import load_dotenv

load_dotenv()

r = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/recipes", response_model=list[RecipeResponse])
def get_recipes(db: Session = Depends(get_session)):
    return db.exec(select(Recipe)).all()

@app.get("/recipes/{id}", response_model=RecipeWithIngredientsResponse)
def get_recipe(id: int, db: Session = Depends(get_session)):
    recipe = db.get(Recipe, id)
    if not recipe:
        raise HTTPException(404, "Nie znaleziono")
    return recipe

@app.get('/test-celery')
def test_celery():
    task = debug_task.delay()
    return {"task_id": task.id}

@app.post("/trigger-scrape")
def trigger_scrape():
    last_key = r.get("last_scrape_task_id")
    if last_key:
        last_task = celery.AsyncResult(last_key)
        if last_task.status in ["PENDING", "STARTED"]:
            raise HTTPException(409, "Scrape task is already running")
    task = scrape_recipes.delay()
    r.set("last_scrape_task_id", task.id)
    return {"task_id": task.id}

@app.get("/recipe-scrape-status/{task_id}")
def recipe_scrape_status(task_id:str):
    task = celery.AsyncResult(task_id)
    return {
        "task_id": task.id,
        "status": task.status,
        "error": str(task.result) if task.failed() else None
    }