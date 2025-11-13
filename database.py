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
    
    # Ensure ingredientID column exists (for existing databases)
    try:
        from sqlmodel import text
        with Session(engine) as session:
            # Check if column exists
            result = session.exec(text("PRAGMA table_info(ingredients)")).all()
            column_names = [row[1] for row in result]
            if 'ingredientID' not in column_names:
                session.exec(text("ALTER TABLE ingredients ADD COLUMN ingredientID TEXT"))
                session.commit()
                print("Added ingredientID column to existing ingredients table")
    except Exception as e:
        # Column might already exist or table might not exist yet
        pass


def get_session():
    """Get a database session"""
    return Session(engine)




