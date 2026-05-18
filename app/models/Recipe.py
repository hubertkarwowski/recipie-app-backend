from datetime import datetime, timezone
from sqlmodel import ARRAY, TEXT, Column, SQLModel, Field, Relationship
from typing import Optional

class Recipe(SQLModel, table=True):
    id:         Optional[int] = Field(default=None, primary_key=True)
    name:       str           = Field(index=True)
    image_url:  Optional[str] = None
    source_url: Optional[str] = Field(default=None, unique=True)
    labels:     list[str]     = Field(default=[], sa_column=Column(ARRAY(TEXT)))
    calories:   Optional[str] = None
    carbs:      Optional[str] = None
    protein:    Optional[str] = None
    fat:        Optional[str] = None
    created_at: datetime      = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    ingredients: list["Ingredient"] = Relationship(back_populates="recipe")

class Ingredient(SQLModel, table=True):
    id:        Optional[int] = Field(default=None, primary_key=True)
    recipe_id: int           = Field(foreign_key="recipe.id")
    name:      str
    qty:       Optional[str] = None

    recipe: Optional[Recipe] = Relationship(back_populates="ingredients")