#!/usr/bin/env python3
"""
Complete OAuth setup and database build
"""

import os
import sys
import webbrowser
from urllib.parse import urlparse, parse_qs

def complete_oauth_and_build():
    """Complete OAuth setup and build database"""
    print("🍶 SakeMonkey Recipe Database - OAuth Setup")
    print("=" * 50)
    
    try:
        from google_sheets_sync import GoogleSheetsSync
        from google_sheets_config import set_spreadsheet_id
        
        # Set up your Google Sheet ID
        spreadsheet_id = "1dp-fcWV0Mm0audZm-EAsQOjyh-C3f6f6"
        set_spreadsheet_id(spreadsheet_id)
        print(f"✅ Google Sheet ID configured: {spreadsheet_id}")
        
        # Initialize Google Sheets sync
        sync = GoogleSheetsSync()
        sync.set_spreadsheet_id(spreadsheet_id)
        
        print("\n🔐 Starting OAuth authentication...")
        print("This will open your browser for Google authentication.")
        print("Please complete the authentication process.")
        
        # Authenticate (this will open browser)
        if sync.authenticate():
            print("✅ Google Sheets authentication successful!")
            
            # Test connection
            print("\n🧪 Testing connection to your Google Sheet...")
            sheets = sync.list_sheets()
            if sheets:
                print(f"✅ Connected successfully! Found {len(sheets)} sheets:")
                for sheet in sheets:
                    print(f"  - {sheet['title']}")
                
                # Now build the database
                print("\n📊 Building database from Google Sheets...")
                from build_database_from_sheets import DatabaseBuilder
                
                builder = DatabaseBuilder()
                try:
                    # Setup database schema
                    builder.setup_database_schema()
                    
                    # Import data from Google Sheets
                    if builder.import_from_google_sheets():
                        print("\n🎉 Database built successfully from Google Sheets!")
                        builder.show_database_summary()
                        
                        print("\n✅ Setup complete! You can now:")
                        print("1. Run: python gui_app.py")
                        print("2. Use the GUI to manage your sake brewing database")
                        print("3. Sync with Google Sheets anytime")
                        
                        return True
                    else:
                        print("\n❌ Failed to import data from Google Sheets")
                        return False
                        
                finally:
                    builder.close()
            else:
                print("❌ No sheets found in your Google Sheet")
                return False
        else:
            print("❌ Google Sheets authentication failed")
            print("Please check your credentials.json file and try again")
            return False
            
    except ImportError as e:
        print(f"❌ Missing required packages: {e}")
        print("Please install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("This script will help you complete the OAuth setup and build your database.")
    print("Make sure you have completed the Google OAuth authentication first.")
    
    input("\nPress Enter to continue after completing OAuth authentication...")
    
    if complete_oauth_and_build():
        print("\n🎉 Setup completed successfully!")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")

if __name__ == "__main__":
    main()


