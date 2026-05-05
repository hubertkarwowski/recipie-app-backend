from fastapi import Depends, FastAPI
from fastapi.concurrency import asynccontextmanager
from sqlmodel import Session, select
from app.tasks.debug import debug_task
from app.db.engine import create_db, get_session
from app.models.Recipies import Recipies


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield
    
app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

@app.get("/recipies")
def get_recipies(session: Session = Depends(get_session)):
    recipies = session.exec(select(Recipies)).all()
    return recipies

@app.get('/test-celery')
def test_celery():
    task = debug_task.delay()
    return {"task_id": task.id}