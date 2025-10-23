#!/usr/bin/env python3
"""
Configure existing Google Sheet for SakeMonkey Recipe Database
"""

import os
from google_sheets_config import set_spreadsheet_id
from google_sheets_sync import GoogleSheetsSync

def configure_existing_sheet():
    """Configure the system to use an existing Google Sheet"""
    
    print("=== Configure Existing Google Sheet ===")
    print("You have an existing Google Sheet called 'SakeRecipeDataBase.xlsx'")
    print("We need the Google Sheet ID to configure the sync.")
    print()
    print("To find your Google Sheet ID:")
    print("1. Open your Google Sheet in a web browser")
    print("2. Look at the URL - it will look like:")
    print("   https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit#gid=0")
    print("3. Copy the YOUR_SHEET_ID part (the long string between /d/ and /edit)")
    print()
    
    spreadsheet_id = input("Enter your Google Sheet ID: ").strip()
    
    if not spreadsheet_id:
        print("No spreadsheet ID provided. Exiting.")
        return False
    
    # Set the spreadsheet ID in configuration
    set_spreadsheet_id(spreadsheet_id)
    print(f"✓ Spreadsheet ID set to: {spreadsheet_id}")
    
    # Test the connection
    print("\nTesting connection to your Google Sheet...")
    try:
        sync = GoogleSheetsSync()
        sync.set_spreadsheet_id(spreadsheet_id)
        
        if sync.authenticate():
            print("✓ Authentication successful!")
            
            # List sheets to verify connection
            sheets = sync.list_sheets()
            if sheets:
                print(f"✓ Connected to Google Sheet with {len(sheets)} sheets:")
                for sheet in sheets:
                    print(f"  - {sheet['title']}")
                
                # Check if the expected sheets exist
                expected_sheets = ['Ingredients', 'Recipe', 'Starters', 'PublishNotes', 'Formulas']
                existing_sheet_names = [sheet['title'] for sheet in sheets]
                
                print("\nChecking for required sheets:")
                for expected_sheet in expected_sheets:
                    if expected_sheet in existing_sheet_names:
                        print(f"  ✓ {expected_sheet}")
                    else:
                        print(f"  ⚠ {expected_sheet} (not found - will be created)")
                
                print(f"\n✓ Configuration complete!")
                print(f"Google Sheet URL: {sync.get_spreadsheet_url()}")
                print("\nYou can now use the GUI to sync your database with this Google Sheet.")
                return True
            else:
                print("⚠ Connected but no sheets found")
                return False
        else:
            print("✗ Authentication failed")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Main function"""
    if configure_existing_sheet():
        print("\n=== Setup Complete! ===")
        print("Your existing Google Sheet is now configured for sync.")
        print("Run 'python gui_app.py' to use the sync functionality.")
    else:
        print("\n=== Setup Failed ===")
        print("Please check your Google Sheet ID and try again.")

if __name__ == "__main__":
    main()
