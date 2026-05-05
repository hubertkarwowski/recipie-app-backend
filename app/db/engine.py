from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
import os


load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

def create_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session