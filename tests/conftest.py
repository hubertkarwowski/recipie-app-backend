import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, delete

from app.config import settings
from app.db.engine import get_session
from app.main import app
from app.models.Recipe import Ingredient, Recipe
from sqlalchemy import Engine


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(settings.TEST_DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def db_session(test_engine: Engine):
    with Session(test_engine) as session:
        yield session
        session.exec(delete(Ingredient))
        session.exec(delete(Recipe))
        session.commit()


@pytest.fixture
def client(db_session: Session):
    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
