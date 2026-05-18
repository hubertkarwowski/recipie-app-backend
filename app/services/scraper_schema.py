from pydantic import BaseModel
from enum import Enum

class IngredientData(BaseModel):
    name: str
    qty: str | None = None

class Diet(str, Enum):
    vegetarian  = "vegetarian"
    vegan       = "vegan"
    gluten_free = "gluten_free"
    low_sugar   = "low_sugar"
    low_calorie = "low_calorie"
    low_fat     = "low_fat"


class RecipeData(BaseModel):
    title: str
    img: str
    calories: str | None = None
    carbs: str | None = None
    protein: str | None = None
    fat: str | None = None
    diets: list[Diet] = []
    ingredients: list[IngredientData] = []