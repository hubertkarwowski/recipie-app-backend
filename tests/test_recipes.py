from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models.Recipe import Recipe


def test_get_recipes_empty_returns_empty_list(client: TestClient):
    response = client.get("/recipes/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_get_recipe(client: TestClient, db_session: Session):
    recipe = Recipe(name="Test Recipe")
    db_session.add(recipe)
    db_session.commit()
    db_session.refresh(recipe)
    response = client.get(f"/recipes/{recipe.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == recipe.id
    assert response.json()["name"] == recipe.name


def test_get_recipe_not_found(client: TestClient):
    response = client.get("/recipes/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
