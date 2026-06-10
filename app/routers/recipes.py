from fastapi import Depends, HTTPException, APIRouter, Path, Query
from app.db.engine import get_session
from sqlmodel import Session, func, select
from app.schemas import PaginatedResponse, RecipeResponse, RecipeWithIngredientsResponse
from app.models.Recipe import Recipe
from typing import Annotated
from enum import Enum


class RecipeSortBy(str, Enum):
    title = "title"
    created_at = "created_at"


router = APIRouter()


@router.get("/", response_model=PaginatedResponse[RecipeResponse])
def get_recipes(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(le=100, ge=1)] = 20,
    label: Annotated[str | None, Query(max_length=50)] = None,
    sort_by: RecipeSortBy = RecipeSortBy.created_at,
    order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    db: Session = Depends(get_session),
):
    query = select(Recipe)
    count_query = select(func.count()).select_from(Recipe)
    sort_column = getattr(Recipe, sort_by.value)
    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    if label:
        query = query.where(Recipe.labels.any(label))
        count_query = count_query.where(Recipe.labels.any(label))
    total = db.exec(count_query).one()
    recipes = db.exec(query.offset(offset).limit(limit)).all()

    return PaginatedResponse(
        total=total,
        offset=offset,
        limit=limit,
        items=recipes,
    )


@router.get("/{id}", response_model=RecipeWithIngredientsResponse)
def get_recipe(id: Annotated[int, Path(gt=0)], db: Session = Depends(get_session)):
    recipe = db.get(Recipe, id)
    if not recipe:
        raise HTTPException(404, "Nie znaleziono")
    return recipe
