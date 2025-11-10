#!/usr/bin/env python3
"""
Test script to demonstrate database functionality
"""

import sqlite3

def test_database():
    """Test basic database functionality"""
    
    # Connect to database
    conn = sqlite3.connect('sake_recipe_db.sqlite')
    cursor = conn.cursor()
    
    print("=== SakeMonkey Recipe Database Test ===\n")
    
    # Test 1: Count records in each table
    print("1. Record counts:")
    tables = ['ingredients', 'recipe', 'starters', 'publish_notes', 'formulas']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   {table}: {count} records")
    
    # Test 2: Show ingredients by type
    print("\n2. Ingredients by type:")
    cursor.execute("SELECT ingredient_type, COUNT(*) FROM ingredients GROUP BY ingredient_type")
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]} items")
    
    # Test 3: Show recipe styles
    print("\n3. Recipe styles:")
    cursor.execute("SELECT style, COUNT(*) FROM recipe GROUP BY style")
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]} batches")
    
    # Test 4: Show sample recipes with details
    print("\n4. Sample recipes:")
    cursor.execute("""
        SELECT r.batchID, r.style, r.kake, r.koji, r.yeast, r.water_type
        FROM recipe r
        ORDER BY r.batchID
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]} style - Kake: {row[2]}, Koji: {row[3]}, Yeast: {row[4]}, Water: {row[5]}")
    
    # Test 5: Show ingredients with descriptions
    print("\n5. Sample ingredients:")
    cursor.execute("SELECT ingredientID, ingredient_type, description FROM ingredients LIMIT 5")
    for row in cursor.fetchall():
        print(f"   {row[0]} ({row[1]}): {row[2]}")
    
    conn.close()
    print("\n=== Database test completed successfully! ===")

if __name__ == "__main__":
    test_database()
