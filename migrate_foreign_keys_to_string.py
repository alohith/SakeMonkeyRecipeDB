"""
Migration script to convert foreign key columns from INTEGER to TEXT
This handles the change from numeric IDs to string ingredientID/StarterBatch
"""
from sqlmodel import Session, text
from database import engine, get_session

def migrate_foreign_keys_to_string():
    """Convert foreign key columns from INTEGER to TEXT"""
    session = get_session()
    try:
        # For starters table: convert StarterBatch and foreign key columns
        print("Migrating starters table...")
        
        # Check current schema
        result = session.exec(text("PRAGMA table_info(starters)")).all()
        column_info = {row[1]: row[2] for row in result}  # {column_name: type}
        
        # If StarterBatch is INTEGER, we need to migrate
        if column_info.get('StarterBatch') == 'INTEGER':
            print("  Converting StarterBatch from INTEGER to TEXT...")
            # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
            # Step 1: Create new table with correct schema
            session.exec(text("""
                CREATE TABLE starters_new (
                    StarterBatch TEXT PRIMARY KEY,
                    Date DATE,
                    BatchID VARCHAR,
                    Amt_Kake FLOAT,
                    Amt_Koji FLOAT,
                    Amt_water FLOAT,
                    water_type TEXT,
                    Kake TEXT,
                    Koji TEXT,
                    yeast TEXT,
                    lactic_acid FLOAT,
                    MgSO4 FLOAT,
                    KCl FLOAT,
                    temp_C FLOAT
                )
            """))
            
            # Step 2: Copy data, converting StarterBatch to string format
            session.exec(text("""
                INSERT INTO starters_new 
                SELECT 
                    CASE 
                        WHEN StarterBatch IS NULL THEN NULL
                        ELSE 's' || CAST(StarterBatch AS TEXT)
                    END as StarterBatch,
                    Date, BatchID, Amt_Kake, Amt_Koji, Amt_water,
                    CAST(water_type AS TEXT) as water_type,
                    CAST(Kake AS TEXT) as Kake,
                    CAST(Koji AS TEXT) as Koji,
                    CAST(yeast AS TEXT) as yeast,
                    lactic_acid, MgSO4, KCl, temp_C
                FROM starters
            """))
            
            # Step 3: Drop old table and rename new one
            session.exec(text("DROP TABLE starters"))
            session.exec(text("ALTER TABLE starters_new RENAME TO starters"))
            print("  [OK] Starters table migrated")
        
        # For recipe table: convert foreign key columns
        print("Migrating recipe table...")
        result = session.exec(text("PRAGMA table_info(recipe)")).all()
        column_info = {row[1]: row[2] for row in result}
        
        if column_info.get('kake') == 'INTEGER' or column_info.get('starter') == 'INTEGER':
            print("  Converting foreign keys from INTEGER to TEXT...")
            # Create new table
            session.exec(text("""
                CREATE TABLE recipe_new (
                    batchID VARCHAR PRIMARY KEY,
                    start_date DATE,
                    pouch_date DATE,
                    batch INTEGER,
                    style VARCHAR,
                    kake TEXT,
                    koji TEXT,
                    yeast TEXT,
                    starter TEXT,
                    water_type TEXT,
                    total_kake_g FLOAT,
                    total_koji_g FLOAT,
                    total_water_mL FLOAT,
                    ferment_temp_C FLOAT,
                    Addition1_Notes VARCHAR,
                    Addition2_Notes VARCHAR,
                    Addition3_Notes VARCHAR,
                    ferment_finish_gravity FLOAT,
                    ferment_finish_brix FLOAT,
                    final_measured_temp_C FLOAT,
                    final_measured_gravity FLOAT,
                    final_measured_Brix_pct FLOAT,
                    final_gravity FLOAT,
                    ABV_pct FLOAT,
                    SMV FLOAT,
                    final_water_addition_mL FLOAT,
                    clarified BOOLEAN,
                    pasteurized BOOLEAN,
                    pasteurization_notes VARCHAR,
                    finishing_additions VARCHAR
                )
            """))
            
            # Copy data, converting foreign keys to strings
            session.exec(text("""
                INSERT INTO recipe_new 
                SELECT 
                    batchID, start_date, pouch_date, batch, style,
                    CAST(kake AS TEXT) as kake,
                    CAST(koji AS TEXT) as koji,
                    CAST(yeast AS TEXT) as yeast,
                    CASE 
                        WHEN starter IS NULL THEN NULL
                        ELSE 's' || CAST(starter AS TEXT)
                    END as starter,
                    CAST(water_type AS TEXT) as water_type,
                    total_kake_g, total_koji_g, total_water_mL, ferment_temp_C,
                    Addition1_Notes, Addition2_Notes, Addition3_Notes,
                    ferment_finish_gravity, ferment_finish_brix,
                    final_measured_temp_C, final_measured_gravity,
                    final_measured_Brix_pct, final_gravity, ABV_pct, SMV,
                    final_water_addition_mL, clarified, pasteurized,
                    pasteurization_notes, finishing_additions
                FROM recipe
            """))
            
            session.exec(text("DROP TABLE recipe"))
            session.exec(text("ALTER TABLE recipe_new RENAME TO recipe"))
            print("  [OK] Recipe table migrated")
        
        # For publishnotes table: convert Water foreign key
        print("Migrating publishnotes table...")
        result = session.exec(text("PRAGMA table_info(publishnotes)")).all()
        column_info = {row[1]: row[2] for row in result}
        
        if column_info.get('Water') == 'INTEGER':
            print("  Converting Water foreign key from INTEGER to TEXT...")
            session.exec(text("""
                CREATE TABLE publishnotes_new (
                    BatchID VARCHAR PRIMARY KEY,
                    Pouch_Date DATE,
                    Style VARCHAR,
                    Water TEXT,
                    ABV FLOAT,
                    SMV FLOAT,
                    Batch_Size_L FLOAT,
                    Rice VARCHAR,
                    Description VARCHAR
                )
            """))
            
            session.exec(text("""
                INSERT INTO publishnotes_new 
                SELECT 
                    BatchID, Pouch_Date, Style,
                    CAST(Water AS TEXT) as Water,
                    ABV, SMV, Batch_Size_L, Rice, Description
                FROM publishnotes
            """))
            
            session.exec(text("DROP TABLE publishnotes"))
            session.exec(text("ALTER TABLE publishnotes_new RENAME TO publishnotes"))
            print("  [OK] PublishNotes table migrated")
        
        session.commit()
        print("\n[OK] Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Starting foreign key migration (INTEGER -> TEXT)...")
    migrate_foreign_keys_to_string()

