"""
Database initialization and connection management
"""
from sqlmodel import SQLModel, create_engine, Session
from models import Ingredient, Recipe, Starter, PublishNote
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "sake_recipe_db.sqlite")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(DATABASE_URL, echo=False)


def init_database():
    """Initialize the database by creating all tables"""
    SQLModel.metadata.create_all(engine)
    print(f"Database initialized at {DB_PATH}")


def get_session():
    """Get a database session"""
    return Session(engine)




