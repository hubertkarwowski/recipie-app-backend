from fastapi import FastAPI
from app.db.engine import create_db
from app.routers.recipes import router as recipes_router
from app.routers.scrape_jobs import router as scrape_jobs_router
from contextlib import asynccontextmanager
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    create_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(router=recipes_router, prefix="/recipes", tags=["Recipes"])
app.include_router(router=scrape_jobs_router, tags=["Scrape Jobs"])
