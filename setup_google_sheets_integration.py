#!/usr/bin/env python3
"""
Setup Google Sheets Integration for SakeMonkey Recipe Database
"""

import os
import sys

def check_google_sheets_packages():
    """Check if Google Sheets packages are installed"""
    print("🔍 Checking Google Sheets packages...")
    
    try:
        import google.auth
        import googleapiclient.discovery
        print("✅ Google Sheets packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing packages: {e}")
        print("\nTo install required packages, run:")
        print("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return False

def check_credentials():
    """Check if credentials.json exists"""
    print("\n🔐 Checking Google API credentials...")
    
    if os.path.exists('credentials.json'):
        print("✅ credentials.json found")
        return True
    else:
        print("❌ credentials.json not found")
        print("\nTo get credentials.json:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Google Sheets API")
        print("4. Create OAuth 2.0 credentials (Desktop application)")
        print("5. Download the JSON file")
        print("6. Rename it to 'credentials.json' and place in this directory")
        return False

def setup_spreadsheet_id():
    """Setup Google Spreadsheet ID"""
    print("\n📊 Setting up Google Spreadsheet ID...")
    
    # Your Google Sheet ID from the URL you provided
    spreadsheet_id = "1dp-fcWV0Mm0audZm-EAsQOjyh-C3f6f6"
    
    try:
        from google_sheets_config import set_spreadsheet_id
        set_spreadsheet_id(spreadsheet_id)
        print(f"✅ Spreadsheet ID configured: {spreadsheet_id}")
        print(f"📋 Google Sheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        return True
    except ImportError:
        print("❌ google_sheets_config module not found")
        return False

def test_google_sheets_connection():
    """Test connection to Google Sheets"""
    print("\n🧪 Testing Google Sheets connection...")
    
    try:
        from google_sheets_sync import GoogleSheetsSync
        from google_sheets_config import get_spreadsheet_id
        
        sync = GoogleSheetsSync()
        spreadsheet_id = get_spreadsheet_id()
        
        if not spreadsheet_id:
            print("❌ No spreadsheet ID configured")
            return False
        
        sync.set_spreadsheet_id(spreadsheet_id)
        
        if sync.authenticate():
            print("✅ Google Sheets authentication successful")
            
            # Test listing sheets
            sheets = sync.list_sheets()
            if sheets:
                print(f"✅ Connected to Google Sheet with {len(sheets)} sheets:")
                for sheet in sheets:
                    print(f"  - {sheet['title']}")
                return True
            else:
                print("❌ No sheets found")
                return False
        else:
            print("❌ Google Sheets authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

def main():
    """Main setup function"""
    print("🍶 SakeMonkey Recipe Database - Google Sheets Setup")
    print("=" * 60)
    
    # Check packages
    if not check_google_sheets_packages():
        print("\n❌ Please install required packages first")
        return False
    
    # Check credentials
    if not check_credentials():
        print("\n❌ Please set up Google API credentials first")
        return False
    
    # Setup spreadsheet ID
    if not setup_spreadsheet_id():
        print("\n❌ Failed to setup spreadsheet ID")
        return False
    
    # Test connection
    if not test_google_sheets_connection():
        print("\n❌ Failed to connect to Google Sheets")
        return False
    
    print("\n🎉 Google Sheets integration setup complete!")
    print("\nNext steps:")
    print("1. Run: python build_database_from_sheets.py")
    print("2. This will build your database from Google Sheets data")
    print("3. Then run: python gui_app.py")
    
    return True

if __name__ == "__main__":
    main()



