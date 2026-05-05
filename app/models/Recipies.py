from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY, TEXT

class Recipies(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    image_url: str | None = None
    source_url: str | None = None
    labels: list[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))

    # ingredients: list["Ingredients"] = Relationship(back_populates="recipe")