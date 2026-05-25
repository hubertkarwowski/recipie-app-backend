# app/schemas.py
from sqlmodel import SQLModel
from app.models.Recipe import Ingredient

class RecipeResponse(SQLModel):
    id:        int
    name:      str
    image_url: str | None
    source_url: str | None
    calories:  str | None
    carbs:     str | None
    protein:   str | None
    fat:       str | None
    labels:    list[str]

class RecipeWithIngredientsResponse(RecipeResponse):
    ingredients: list[Ingredient] = []