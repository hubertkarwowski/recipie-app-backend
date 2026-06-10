# app/schemas.py
from datetime import datetime
from typing import Generic, TypeVar

from sqlmodel import SQLModel
from app.models.Recipe import Ingredient

T = TypeVar("T")


class PaginatedResponse(SQLModel, Generic[T]):
    total: int
    items: list[T]
    offset: int
    limit: int


class RecipeResponse(SQLModel):
    id: int
    name: str
    image_url: str | None
    source_url: str | None
    calories: str | None
    carbs: str | None
    protein: str | None
    fat: str | None
    labels: list[str]
    created_at: datetime


class RecipeWithIngredientsResponse(RecipeResponse):
    ingredients: list[Ingredient] = []
