"""
Migration script to add ingredientID column to ingredients table
Run this once to update the database schema
"""
from sqlmodel import Session, text
from database import engine, get_session

def migrate_add_ingredientid():
    """Add ingredientID column to ingredients table if it doesn't exist"""
    session = get_session()
    try:
        # Check if column already exists
        result = session.exec(
            text("PRAGMA table_info(ingredients)")
        ).all()
        
        column_names = [row[1] for row in result]  # Column name is at index 1
        
        if 'ingredientID' in column_names:
            print("Column 'ingredientID' already exists. No migration needed.")
            return
        
        # Add the column
        print("Adding 'ingredientID' column to ingredients table...")
        session.exec(
            text("ALTER TABLE ingredients ADD COLUMN ingredientID TEXT")
        )
        session.commit()
        print("[OK] Migration completed successfully! Column 'ingredientID' added.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Running migration to add ingredientID column...")
    migrate_add_ingredientid()
    print("\nMigration complete! You can now run gooey_interface.py")

