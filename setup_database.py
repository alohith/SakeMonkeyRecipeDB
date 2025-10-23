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
            acc_date TEXT,
            source TEXT,
            description TEXT
        )
    ''')
    
    # Create Recipe table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT,
            pouch_date TEXT,
            batchID TEXT UNIQUE NOT NULL,
            batch TEXT,
            style TEXT,
            kake TEXT,
            koji TEXT,
            yeast TEXT,
            starter TEXT,
            water_type TEXT,
            FOREIGN KEY (kake) REFERENCES ingredients(ingredientID),
            FOREIGN KEY (koji) REFERENCES ingredients(ingredientID),
            FOREIGN KEY (yeast) REFERENCES ingredients(ingredientID)
        )
    ''')
    
    # Create Starters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS starters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            starter_batch TEXT,
            batchID TEXT,
            amt_kake REAL,
            amt_koji REAL,
            amt_water REAL,
            water_type TEXT,
            kake TEXT,
            koji TEXT,
            yeast TEXT,
            FOREIGN KEY (batchID) REFERENCES recipe(batchID),
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
            pouch_date TEXT,
            style TEXT,
            water TEXT,
            abv REAL,
            smv REAL,
            batch_size_l REAL,
            rice TEXT,
            description TEXT,
            FOREIGN KEY (batchID) REFERENCES recipe(batchID)
        )
    ''')
    
    # Create Formulas table for brewing calculations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            measure_temp_c REAL,
            measured_sg REAL,
            measured_brix REAL,
            final_sg REAL,
            abv REAL,
            smv REAL,
            brix REAL,
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
