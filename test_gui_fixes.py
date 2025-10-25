#!/usr/bin/env python3
"""
Test script to verify GUI fixes and database schema
"""

import sqlite3
import sys

def test_database_schema():
    """Test that all required columns exist in the database"""
    try:
        conn = sqlite3.connect('sake_recipe_db.sqlite')
        cursor = conn.cursor()
        
        # Test starters table
        cursor.execute("PRAGMA table_info(starters)")
        starters_columns = [row[1] for row in cursor.fetchall()]
        required_starters = ['lactic_acid', 'MgSO4', 'KCl', 'temp_C']
        
        print("Testing Starters table...")
        for col in required_starters:
            if col in starters_columns:
                print(f"✅ {col} column exists")
            else:
                print(f"❌ {col} column missing")
                return False
        
        # Test recipe table
        cursor.execute("PRAGMA table_info(recipe)")
        recipe_columns = [row[1] for row in cursor.fetchall()]
        required_recipe = ['total_kake_g', 'total_koji_g', 'total_water_mL', 'ferment_temp_C', 
                          'addition1_notes', 'addition2_notes', 'addition3_notes',
                          'final_measured_temp_C', 'final_measured_gravity', 'final_measured_brix',
                          'clarified', 'pasteurized']
        
        print("\nTesting Recipe table...")
        for col in required_recipe:
            if col in recipe_columns:
                print(f"✅ {col} column exists")
            else:
                print(f"❌ {col} column missing")
                return False
        
        # Test formulas table
        cursor.execute("PRAGMA table_info(formulas)")
        formulas_columns = [row[1] for row in cursor.fetchall()]
        required_formulas = ['calibrated_temp_c', 'measured_temp_c', 'measured_sg', 'measured_brix',
                            'corrected_gravity', 'calculated_abv', 'calculated_smv']
        
        print("\nTesting Formulas table...")
        for col in required_formulas:
            if col in formulas_columns:
                print(f"✅ {col} column exists")
            else:
                print(f"❌ {col} column missing")
                return False
        
        conn.close()
        print("\n✅ All database schema tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_sample_data_insertion():
    """Test inserting sample data to verify schema works"""
    try:
        conn = sqlite3.connect('sake_recipe_db.sqlite')
        cursor = conn.cursor()
        
        # Test inserting a starter with new fields
        cursor.execute("""
            INSERT INTO starters (date, starter_batch, batchID, amt_kake, amt_koji, amt_water, 
                                 water_type, kake, koji, yeast, lactic_acid, MgSO4, KCl, temp_C)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('2024-01-01', 'ST001', 'B001', 100.0, 50.0, 200.0, 'spring', 'rice1', 'rice1', 'yeast1', 
              2.0, 1.0, 0.5, 20.0))
        
        # Test inserting a recipe with new fields
        cursor.execute("""
            INSERT INTO recipe (batchID, batch, style, kake, koji, yeast, starter, water_type,
                               start_date, pouch_date, total_kake_g, total_koji_g, total_water_mL,
                               ferment_temp_C, addition1_notes, addition2_notes, addition3_notes,
                               final_measured_temp_C, final_measured_gravity, final_measured_brix,
                               clarified, pasteurized)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('B001', 1, 'pure', 'rice1', 'rice1', 'yeast1', 'ST001', 'spring',
              '2024-01-01', '2024-01-15', 500.0, 250.0, 1000.0, 18.0,
              'First addition notes', 'Second addition notes', 'Third addition notes',
              20.0, 1.020, 15.5, True, False))
        
        # Test inserting a formula calculation
        cursor.execute("""
            INSERT INTO formulas (calibrated_temp_c, measured_temp_c, measured_sg, measured_brix,
                                 corrected_gravity, calculated_abv, calculated_smv)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (20.0, 25.0, 1.020, 15.5, 1.018, 8.5, -3.2))
        
        conn.commit()
        conn.close()
        
        print("✅ Sample data insertion test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Sample data insertion failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Testing GUI Fixes ===")
    
    # Test database schema
    if not test_database_schema():
        print("❌ Database schema test failed!")
        sys.exit(1)
    
    # Test sample data insertion
    if not test_sample_data_insertion():
        print("❌ Sample data insertion test failed!")
        sys.exit(1)
    
    print("\n🎉 All tests passed! GUI should work correctly now.")

if __name__ == "__main__":
    main()
