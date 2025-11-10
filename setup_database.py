#!/usr/bin/env python3
"""
Database setup script for SakeMonkey Recipe Database
Creates SQLite database with schema based on Excel data structure
"""

import sqlite3
import os

def create_database():
    """Create the SQLite database with all required tables"""
    
    # Connect to database (creates if doesn't exist)
    conn = sqlite3.connect('sake_recipe_db.sqlite')
    cursor = conn.cursor()
    
    # Create Ingredients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            ingredientID TEXT PRIMARY KEY,
            ingredient_type TEXT NOT NULL,
            acc_date DATE,
            source TEXT,
            description TEXT
        )
    ''')
    
    # Create Recipe table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date DATE,
            pouch_date DATE,
            batchID TEXT UNIQUE NOT NULL,
            batch INTEGER,
            style TEXT CHECK(style IN ('pure', 'rustic', 'rustic_experimental')),
            kake TEXT,
            koji TEXT,
            yeast TEXT,
            starter TEXT,
            water_type TEXT,
            total_kake_g REAL,
            total_koji_g REAL,
            total_water_mL REAL,
            ferment_temp_C REAL,
            addition1_notes TEXT,
            addition2_notes TEXT,
            addition3_notes TEXT,
            ferment_finish_gravity REAL,
            ferment_finish_brix REAL,
            final_measured_temp_C REAL,
            final_measured_gravity REAL,
            final_measured_brix REAL,
            final_gravity REAL,
            abv REAL,
            smv REAL,
            final_water_addition_mL REAL,
            clarified BOOLEAN,
            pasteurized BOOLEAN,
            pasteurization_notes TEXT,
            finishing_additions TEXT,
            FOREIGN KEY (kake) REFERENCES ingredients(ingredientID),
            FOREIGN KEY (koji) REFERENCES ingredients(ingredientID),
            FOREIGN KEY (yeast) REFERENCES ingredients(ingredientID),
            FOREIGN KEY (starter) REFERENCES starters(starter_batch),
            FOREIGN KEY (water_type) REFERENCES ingredients(ingredientID)
        )
    ''')
    
    # Create Starters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS starters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            starter_batch TEXT,
            batchID TEXT,
            amt_kake REAL,
            amt_koji REAL,
            amt_water REAL,
            water_type TEXT,
            kake TEXT,
            koji TEXT,
            yeast TEXT,
            lactic_acid REAL,
            MgSO4 REAL,
            KCl REAL,
            temp_C REAL,
            FOREIGN KEY (batchID) REFERENCES recipe(batchID),
            FOREIGN KEY (water_type) REFERENCES ingredients(ingredientID),
            FOREIGN KEY (kake) REFERENCES ingredients(ingredientID),
            FOREIGN KEY (koji) REFERENCES ingredients(ingredientID),
            FOREIGN KEY (yeast) REFERENCES ingredients(ingredientID)
        )
    ''')
    
    # Create PublishNotes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS publish_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batchID TEXT,
            pouch_date DATE,
            style TEXT CHECK(style IN ('pure', 'rustic', 'rustic_experimental')),
            water TEXT,
            abv REAL,
            smv REAL,
            batch_size_l REAL,
            rice TEXT,
            description TEXT,
            FOREIGN KEY (batchID) REFERENCES recipe(batchID),
            FOREIGN KEY (water) REFERENCES ingredients(ingredientID)
        )
    ''')
    
    # Create Formulas table for brewing calculations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calibrated_temp_c REAL DEFAULT 20.0,
            measured_temp_c REAL,
            measured_sg REAL,
            measured_brix REAL,
            corrected_gravity REAL,
            calculated_abv REAL,
            calculated_smv REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_recipe_batchID ON recipe(batchID)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingredients_type ON ingredients(ingredient_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_starters_batchID ON starters(batchID)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_publish_batchID ON publish_notes(batchID)')
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("Database created successfully: sake_recipe_db.sqlite")
    print("Tables created:")
    print("- ingredients")
    print("- recipe") 
    print("- starters")
    print("- publish_notes")
    print("- formulas")

if __name__ == "__main__":
    create_database()
