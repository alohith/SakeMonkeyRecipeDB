#!/usr/bin/env python3
"""
Database interface for SakeMonkey Recipe Database
Provides basic CRUD operations and queries
"""

import sqlite3
import os
from datetime import datetime

class SakeRecipeDB:
    def __init__(self, db_path='sake_recipe_db.sqlite'):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Connect to the database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
    
    def disconnect(self):
        """Disconnect from the database"""
        if self.conn:
            self.conn.close()
    
    def get_all_ingredients(self):
        """Get all ingredients"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM ingredients ORDER BY ingredient_type, ingredientID")
        return cursor.fetchall()
    
    def get_ingredients_by_type(self, ingredient_type):
        """Get ingredients by type"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM ingredients WHERE ingredient_type = ?", (ingredient_type,))
        return cursor.fetchall()
    
    def get_all_recipes(self):
        """Get all recipes"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT r.*, 
                   i_kake.description as kake_desc,
                   i_koji.description as koji_desc,
                   i_yeast.description as yeast_desc
            FROM recipe r
            LEFT JOIN ingredients i_kake ON r.kake = i_kake.ingredientID
            LEFT JOIN ingredients i_koji ON r.koji = i_koji.ingredientID
            LEFT JOIN ingredients i_yeast ON r.yeast = i_yeast.ingredientID
            ORDER BY r.batchID
        """)
        return cursor.fetchall()
    
    def get_recipe_by_batch(self, batchID):
        """Get recipe by batch ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM recipe WHERE batchID = ?", (batchID,))
        return cursor.fetchone()
    
    def get_starters_for_batch(self, batchID):
        """Get starters for a specific batch"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM starters WHERE batchID = ?", (batchID,))
        return cursor.fetchall()
    
    def get_publish_notes_for_batch(self, batchID):
        """Get publish notes for a specific batch"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM publish_notes WHERE batchID = ?", (batchID,))
        return cursor.fetchone()
    
    def add_ingredient(self, ingredientID, ingredient_type, description, source=None, acc_date=None):
        """Add a new ingredient"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO ingredients (ingredientID, ingredient_type, acc_date, source, description)
            VALUES (?, ?, ?, ?, ?)
        """, (ingredientID, ingredient_type, acc_date, source, description))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_recipe(self, batchID, batch, style, kake, koji, yeast, starter=None, 
                   water_type=None, start_date=None, pouch_date=None):
        """Add a new recipe"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO recipe (batchID, batch, style, kake, koji, yeast, starter, 
                               water_type, start_date, pouch_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (batchID, batch, style, kake, koji, yeast, starter, 
              water_type, start_date, pouch_date))
        self.conn.commit()
        return cursor.lastrowid
    
    def search_recipes_by_style(self, style):
        """Search recipes by style"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM recipe WHERE style LIKE ?", (f'%{style}%',))
        return cursor.fetchall()
    
    def get_recipe_summary(self):
        """Get a summary of all recipes with key information"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT r.batchID, r.batch, r.style, r.start_date, r.pouch_date,
                   pn.abv, pn.smv, pn.batch_size_l
            FROM recipe r
            LEFT JOIN publish_notes pn ON r.batchID = pn.batchID
            ORDER BY r.batchID
        """)
        return cursor.fetchall()

def main():
    """Main interface for database operations"""
    db = SakeRecipeDB()
    
    if not os.path.exists(db.db_path):
        print("Database not found. Please run setup_database.py first.")
        return
    
    try:
        db.connect()
        
        while True:
            print("\n=== SakeMonkey Recipe Database ===")
            print("1. View all ingredients")
            print("2. View all recipes")
            print("3. Search recipes by style")
            print("4. Get recipe details")
            print("5. View recipe summary")
            print("6. Add new ingredient")
            print("7. Add new recipe")
            print("8. Exit")
            
            choice = input("\nEnter your choice (1-8): ").strip()
            
            if choice == '1':
                ingredients = db.get_all_ingredients()
                print(f"\nFound {len(ingredients)} ingredients:")
                for ing in ingredients:
                    print(f"- {ing['ingredientID']}: {ing['ingredient_type']} - {ing['description']}")
            
            elif choice == '2':
                recipes = db.get_all_recipes()
                print(f"\nFound {len(recipes)} recipes:")
                for recipe in recipes:
                    print(f"- {recipe['batchID']}: {recipe['style']} style, Batch {recipe['batch']}")
            
            elif choice == '3':
                style = input("Enter style to search for: ").strip()
                recipes = db.search_recipes_by_style(style)
                print(f"\nFound {len(recipes)} recipes with style '{style}':")
                for recipe in recipes:
                    print(f"- {recipe['batchID']}: {recipe['style']} style")
            
            elif choice == '4':
                batchID = input("Enter batch ID: ").strip()
                recipe = db.get_recipe_by_batch(batchID)
                if recipe:
                    print(f"\nRecipe Details for {batchID}:")
                    print(f"Style: {recipe['style']}")
                    print(f"Kake: {recipe['kake']}")
                    print(f"Koji: {recipe['koji']}")
                    print(f"Yeast: {recipe['yeast']}")
                    print(f"Water Type: {recipe['water_type']}")
                else:
                    print(f"No recipe found for batch {batchID}")
            
            elif choice == '5':
                summary = db.get_recipe_summary()
                print(f"\nRecipe Summary ({len(summary)} recipes):")
                for recipe in summary:
                    print(f"- {recipe['batchID']}: {recipe['style']} | ABV: {recipe['abv']} | SMV: {recipe['smv']}")
            
            elif choice == '6':
                print("\nAdd new ingredient:")
                ingredientID = input("Ingredient ID: ").strip()
                ingredient_type = input("Type (yeast/koji_rice/kake_rice/etc): ").strip()
                description = input("Description: ").strip()
                source = input("Source (optional): ").strip() or None
                
                try:
                    db.add_ingredient(ingredientID, ingredient_type, description, source)
                    print("Ingredient added successfully!")
                except sqlite3.IntegrityError:
                    print("Error: Ingredient ID already exists")
            
            elif choice == '7':
                print("\nAdd new recipe:")
                batchID = input("Batch ID: ").strip()
                batch = input("Batch number: ").strip()
                style = input("Style: ").strip()
                kake = input("Kake ingredient ID: ").strip()
                koji = input("Koji ingredient ID: ").strip()
                yeast = input("Yeast ingredient ID: ").strip()
                
                try:
                    db.add_recipe(batchID, batch, style, kake, koji, yeast)
                    print("Recipe added successfully!")
                except sqlite3.IntegrityError:
                    print("Error: Batch ID already exists")
            
            elif choice == '8':
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice. Please try again.")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        db.disconnect()

if __name__ == "__main__":
    main()
