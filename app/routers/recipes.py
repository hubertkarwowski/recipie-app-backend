from fastapi import Depends, HTTPException, APIRouter
from app.db.engine import get_session
from sqlmodel import Session, select
from app.schemas import RecipeResponse, RecipeWithIngredientsResponse
from app.models.Recipe import Recipe

router = APIRouter()

@router.get("/", response_model=list[RecipeResponse])
def get_recipes(db: Session = Depends(get_session)):
    return db.exec(select(Recipe)).all()

@router.get("/{id}", response_model=RecipeWithIngredientsResponse)
def get_recipe(id: int, db: Session = Depends(get_session)):
    recipe = db.get(Recipe, id)
    if not recipe:
        raise HTTPException(404, "Nie znaleziono")
    return recipe