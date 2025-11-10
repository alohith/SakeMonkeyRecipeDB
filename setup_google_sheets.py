#!/usr/bin/env python3
"""
Setup script for Google Sheets integration
Helps configure Google Sheets API credentials and spreadsheet
"""

import os
import json
import webbrowser
from google_sheets_sync import GoogleSheetsSync
from google_sheets_config import set_spreadsheet_id

def check_credentials():
    """Check if credentials file exists"""
    if os.path.exists('credentials.json'):
        print("✓ credentials.json found")
        return True
    else:
        print("✗ credentials.json not found")
        return False

def setup_credentials():
    """Guide user through credentials setup"""
    print("\n=== Google Sheets API Credentials Setup ===")
    print("To set up Google Sheets integration, you need to:")
    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Create a new project or select an existing one")
    print("3. Enable the Google Sheets API")
    print("4. Create OAuth 2.0 credentials")
    print("5. Download the credentials JSON file")
    print("\nDetailed steps:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Click 'Select a project' and create/select a project")
    print("3. Go to 'APIs & Services' > 'Library'")
    print("4. Search for 'Google Sheets API' and enable it")
    print("5. Go to 'APIs & Services' > 'Credentials'")
    print("6. Click 'Create Credentials' > 'OAuth 2.0 Client ID'")
    print("7. Choose 'Desktop application'")
    print("8. Download the JSON file")
    print("9. Rename it to 'credentials.json' and place in this directory")
    
    input("\nPress Enter when you have completed these steps...")

def test_authentication():
    """Test Google Sheets authentication"""
    print("\n=== Testing Authentication ===")
    try:
        sync = GoogleSheetsSync()
        if sync.authenticate():
            print("✓ Authentication successful!")
            return sync
        else:
            print("✗ Authentication failed")
            return None
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        return None

def setup_spreadsheet(sync):
    """Setup or create Google Spreadsheet"""
    print("\n=== Spreadsheet Setup ===")
    
    choice = input("Do you want to:\n1. Create a new spreadsheet\n2. Use an existing spreadsheet\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        # Create new spreadsheet
        print("Creating new spreadsheet...")
        spreadsheet_id = sync.create_spreadsheet()
        if spreadsheet_id:
            print(f"✓ Created new spreadsheet: {sync.get_spreadsheet_url()}")
            set_spreadsheet_id(spreadsheet_id)
            return spreadsheet_id
        else:
            print("✗ Failed to create spreadsheet")
            return None
    
    elif choice == "2":
        # Use existing spreadsheet
        spreadsheet_id = input("Enter your Google Spreadsheet ID: ").strip()
        if spreadsheet_id:
            sync.set_spreadsheet_id(spreadsheet_id)
            set_spreadsheet_id(spreadsheet_id)
            print(f"✓ Using spreadsheet: {sync.get_spreadsheet_url()}")
            return spreadsheet_id
        else:
            print("✗ No spreadsheet ID provided")
            return None
    
    else:
        print("✗ Invalid choice")
        return None

def test_sync(sync):
    """Test sync functionality"""
    print("\n=== Testing Sync ===")
    
    if not sync.spreadsheet_id:
        print("✗ No spreadsheet ID set")
        return False
    
    try:
        # Test export
        print("Testing export to Google Sheets...")
        if sync.export_to_sheets():
            print("✓ Export test successful!")
        else:
            print("✗ Export test failed!")
            return False
        
        # Test import
        print("Testing import from Google Sheets...")
        if sync.import_from_sheets():
            print("✓ Import test successful!")
        else:
            print("✗ Import test failed!")
            return False
        
        print("✓ All sync tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Sync test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=== SakeMonkey Recipe Database - Google Sheets Setup ===")
    
    # Check credentials
    if not check_credentials():
        setup_credentials()
        if not check_credentials():
            print("Please complete the credentials setup and run this script again.")
            return
    
    # Test authentication
    sync = test_authentication()
    if not sync:
        print("Please fix authentication issues and run this script again.")
        return
    
    # Setup spreadsheet
    spreadsheet_id = setup_spreadsheet(sync)
    if not spreadsheet_id:
        print("Please fix spreadsheet setup and run this script again.")
        return
    
    # Test sync
    if test_sync(sync):
        print("\n=== Setup Complete! ===")
        print("Google Sheets integration is now configured.")
        print(f"Spreadsheet URL: {sync.get_spreadsheet_url()}")
        print("\nYou can now use the GUI to sync your database with Google Sheets.")
    else:
        print("\n=== Setup Incomplete ===")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    main()
