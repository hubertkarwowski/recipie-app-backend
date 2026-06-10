from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
from app.config import settings


engine = create_engine(settings.DATABASE_URL, echo=True)


def create_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
