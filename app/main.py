from fastapi import FastAPI
from app.routers.recipes import router as recipes_router
from app.routers.scrape_jobs import router as scrape_jobs_router

app = FastAPI()

app.include_router(router=recipes_router, prefix='/recipes', tags=["Recipes"])
app.include_router(router=scrape_jobs_router, tags=["Scrape Jobs"])
