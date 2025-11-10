#!/usr/bin/env python3
"""
Build SakeMonkey Recipe Database from Google Sheets
Uses the table rules from rules.txt and populates from Google Sheet
"""

import sqlite3
import os
import sys
from datetime import datetime
import json

# Import Google Sheets functionality
try:
    from google_sheets_sync import GoogleSheetsSync
    from google_sheets_config import get_spreadsheet_id
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("Google Sheets integration not available. Install required packages:")
    print("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

class DatabaseBuilder:
    def __init__(self):
        self.db_path = 'sake_recipe_db.sqlite'
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        if GOOGLE_SHEETS_AVAILABLE:
            self.google_sync = GoogleSheetsSync()
        else:
            self.google_sync = None
    
    def setup_database_schema(self):
        """Setup database schema based on rules.txt"""
        print("🔧 Setting up database schema...")
        
        cursor = self.conn.cursor()
        
        # Create Ingredients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingredients (
                ingredientID TEXT PRIMARY KEY,
                ingredient_type TEXT NOT NULL CHECK(ingredient_type IN ('yeast', 'rice', 'nutrientMix', 'water', 'other')),
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
        
        # Create Formulas table
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
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_recipe_batchID ON recipe(batchID)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingredients_type ON ingredients(ingredient_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_starters_batchID ON starters(batchID)')
        
        self.conn.commit()
        print("✅ Database schema created successfully")
    
    def authenticate_google_sheets(self):
        """Authenticate with Google Sheets"""
        if not GOOGLE_SHEETS_AVAILABLE:
            print("❌ Google Sheets not available")
            return False
        
        print("🔐 Authenticating with Google Sheets...")
        
        # Check if credentials exist
        if not os.path.exists('credentials.json'):
            print("❌ credentials.json not found")
            print("Please download credentials.json from Google Cloud Console")
            return False
        
        # Authenticate
        if self.google_sync.authenticate():
            print("✅ Google Sheets authentication successful")
            return True
        else:
            print("❌ Google Sheets authentication failed")
            return False
    
    def import_from_google_sheets(self):
        """Import data from Google Sheets"""
        if not self.google_sync:
            print("❌ Google Sheets not available")
            return False
        
        print("📊 Importing data from Google Sheets...")
        
        try:
            # Get spreadsheet ID
            spreadsheet_id = get_spreadsheet_id()
            if not spreadsheet_id:
                print("❌ No spreadsheet ID configured")
                return False
            
            self.google_sync.set_spreadsheet_id(spreadsheet_id)
            
            # Import data from each sheet
            success = True
            
            # Import Ingredients
            if self.import_ingredients():
                print("✅ Ingredients imported successfully")
            else:
                print("❌ Failed to import ingredients")
                success = False
            
            # Import Recipes
            if self.import_recipes():
                print("✅ Recipes imported successfully")
            else:
                print("❌ Failed to import recipes")
                success = False
            
            # Import Starters
            if self.import_starters():
                print("✅ Starters imported successfully")
            else:
                print("❌ Failed to import starters")
                success = False
            
            # Import Publish Notes
            if self.import_publish_notes():
                print("✅ Publish Notes imported successfully")
            else:
                print("❌ Failed to import publish notes")
                success = False
            
            # Import Formulas
            if self.import_formulas():
                print("✅ Formulas imported successfully")
            else:
                print("❌ Failed to import formulas")
                success = False
            
            return success
            
        except Exception as e:
            print(f"❌ Error importing from Google Sheets: {e}")
            return False
    
    def import_ingredients(self):
        """Import ingredients from Google Sheets"""
        try:
            # Get data from Ingredients sheet
            data = self.google_sync.import_from_sheets('Ingredients')
            if not data:
                print("No ingredients data found")
                return False
            
            cursor = self.conn.cursor()
            
            for row in data[1:]:  # Skip header
                if len(row) >= 3 and row[0]:  # Ensure we have at least ID, type, and date
                    cursor.execute("""
                        INSERT OR REPLACE INTO ingredients 
                        (ingredientID, ingredient_type, acc_date, source, description)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        row[0],  # ingredientID
                        row[1],  # ingredient_type
                        row[2],  # acc_date
                        row[3] if len(row) > 3 else None,  # source
                        row[4] if len(row) > 4 else None   # description
                    ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error importing ingredients: {e}")
            return False
    
    def import_recipes(self):
        """Import recipes from Google Sheets"""
        try:
            data = self.google_sync.import_from_sheets('Recipe')
            if not data:
                print("No recipe data found")
                return False
            
            cursor = self.conn.cursor()
            
            for row in data[1:]:  # Skip header
                if len(row) >= 5 and row[0]:  # Ensure we have basic recipe data
                    cursor.execute("""
                        INSERT OR REPLACE INTO recipe 
                        (batchID, batch, style, kake, koji, yeast, starter, water_type,
                         start_date, pouch_date, total_kake_g, total_koji_g, total_water_mL,
                         ferment_temp_C, addition1_notes, addition2_notes, addition3_notes,
                         final_measured_temp_C, final_measured_gravity, final_measured_brix,
                         clarified, pasteurized)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row[0],   # batchID
                        int(row[1]) if row[1] else None,  # batch
                        row[2],   # style
                        row[3],   # kake
                        row[4],   # koji
                        row[5] if len(row) > 5 else None,  # yeast
                        row[6] if len(row) > 6 else None,  # starter
                        row[7] if len(row) > 7 else None,  # water_type
                        row[8] if len(row) > 8 else None,  # start_date
                        row[9] if len(row) > 9 else None,  # pouch_date
                        float(row[10]) if len(row) > 10 and row[10] else None,  # total_kake_g
                        float(row[11]) if len(row) > 11 and row[11] else None,  # total_koji_g
                        float(row[12]) if len(row) > 12 and row[12] else None,  # total_water_mL
                        float(row[13]) if len(row) > 13 and row[13] else None,  # ferment_temp_C
                        row[14] if len(row) > 14 else None,  # addition1_notes
                        row[15] if len(row) > 15 else None,  # addition2_notes
                        row[16] if len(row) > 16 else None,  # addition3_notes
                        float(row[17]) if len(row) > 17 and row[17] else None,  # final_measured_temp_C
                        float(row[18]) if len(row) > 18 and row[18] else None,  # final_measured_gravity
                        float(row[19]) if len(row) > 19 and row[19] else None,  # final_measured_brix
                        bool(row[20]) if len(row) > 20 and row[20] else False,  # clarified
                        bool(row[21]) if len(row) > 21 and row[21] else False   # pasteurized
                    ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error importing recipes: {e}")
            return False
    
    def import_starters(self):
        """Import starters from Google Sheets"""
        try:
            data = self.google_sync.import_from_sheets('Starters')
            if not data:
                print("No starters data found")
                return False
            
            cursor = self.conn.cursor()
            
            for row in data[1:]:  # Skip header
                if len(row) >= 5 and row[0]:  # Ensure we have basic starter data
                    cursor.execute("""
                        INSERT OR REPLACE INTO starters 
                        (date, starter_batch, batchID, amt_kake, amt_koji, amt_water,
                         water_type, kake, koji, yeast, lactic_acid, MgSO4, KCl, temp_C)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row[0],   # date
                        row[1],   # starter_batch
                        row[2],   # batchID
                        float(row[3]) if row[3] else None,  # amt_kake
                        float(row[4]) if row[4] else None,  # amt_koji
                        float(row[5]) if len(row) > 5 and row[5] else None,  # amt_water
                        row[6] if len(row) > 6 else None,   # water_type
                        row[7] if len(row) > 7 else None,   # kake
                        row[8] if len(row) > 8 else None,   # koji
                        row[9] if len(row) > 9 else None,   # yeast
                        float(row[10]) if len(row) > 10 and row[10] else None,  # lactic_acid
                        float(row[11]) if len(row) > 11 and row[11] else None,  # MgSO4
                        float(row[12]) if len(row) > 12 and row[12] else None,  # KCl
                        float(row[13]) if len(row) > 13 and row[13] else None   # temp_C
                    ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error importing starters: {e}")
            return False
    
    def import_publish_notes(self):
        """Import publish notes from Google Sheets"""
        try:
            data = self.google_sync.import_from_sheets('PublishNotes')
            if not data:
                print("No publish notes data found")
                return False
            
            cursor = self.conn.cursor()
            
            for row in data[1:]:  # Skip header
                if len(row) >= 3 and row[0]:  # Ensure we have basic publish notes data
                    cursor.execute("""
                        INSERT OR REPLACE INTO publish_notes 
                        (batchID, pouch_date, style, water, abv, smv, batch_size_l, rice, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row[0],   # batchID
                        row[1],   # pouch_date
                        row[2],   # style
                        row[3] if len(row) > 3 else None,   # water
                        float(row[4]) if len(row) > 4 and row[4] else None,  # abv
                        float(row[5]) if len(row) > 5 and row[5] else None,  # smv
                        float(row[6]) if len(row) > 6 and row[6] else None,  # batch_size_l
                        row[7] if len(row) > 7 else None,   # rice
                        row[8] if len(row) > 8 else None    # description
                    ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error importing publish notes: {e}")
            return False
    
    def import_formulas(self):
        """Import formulas from Google Sheets"""
        try:
            data = self.google_sync.import_from_sheets('Formulas')
            if not data:
                print("No formulas data found")
                return False
            
            cursor = self.conn.cursor()
            
            for row in data[1:]:  # Skip header
                if len(row) >= 3 and row[0]:  # Ensure we have basic formula data
                    cursor.execute("""
                        INSERT OR REPLACE INTO formulas 
                        (calibrated_temp_c, measured_temp_c, measured_sg, measured_brix,
                         corrected_gravity, calculated_abv, calculated_smv)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        float(row[0]) if row[0] else 20.0,  # calibrated_temp_c
                        float(row[1]) if row[1] else None,  # measured_temp_c
                        float(row[2]) if row[2] else None,  # measured_sg
                        float(row[3]) if len(row) > 3 and row[3] else None,  # measured_brix
                        float(row[4]) if len(row) > 4 and row[4] else None,  # corrected_gravity
                        float(row[5]) if len(row) > 5 and row[5] else None,  # calculated_abv
                        float(row[6]) if len(row) > 6 and row[6] else None   # calculated_smv
                    ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error importing formulas: {e}")
            return False
    
    def show_database_summary(self):
        """Show summary of database contents"""
        print("\n📊 Database Summary:")
        print("=" * 50)
        
        cursor = self.conn.cursor()
        
        # Count records in each table
        tables = ['ingredients', 'recipe', 'starters', 'publish_notes', 'formulas']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table.capitalize()}: {count} records")
        
        # Show sample data
        print("\n📋 Sample Ingredients:")
        cursor.execute("SELECT ingredientID, ingredient_type, description FROM ingredients LIMIT 5")
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]}): {row[2] or 'No description'}")
        
        print("\n🍶 Sample Recipes:")
        cursor.execute("SELECT batchID, style, start_date FROM recipe LIMIT 5")
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]}): Started {row[2] or 'Unknown'}")
    
    def close(self):
        """Close database connection"""
        self.conn.close()

def main():
    """Main function"""
    print("🍶 SakeMonkey Recipe Database Builder")
    print("=" * 50)
    
    builder = DatabaseBuilder()
    
    try:
        # Setup database schema
        builder.setup_database_schema()
        
        # Authenticate with Google Sheets
        if builder.authenticate_google_sheets():
            # Import data from Google Sheets
            if builder.import_from_google_sheets():
                print("\n✅ Database built successfully from Google Sheets!")
            else:
                print("\n❌ Failed to import data from Google Sheets")
        else:
            print("\n⚠️  Google Sheets not available - database schema created but not populated")
        
        # Show database summary
        builder.show_database_summary()
        
        print("\n🎉 Database setup complete!")
        print("You can now use the GUI: python gui_app.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    finally:
        builder.close()
    
    return True

if __name__ == "__main__":
    main()


