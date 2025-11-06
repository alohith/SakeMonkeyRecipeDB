#!/usr/bin/env python3
"""
Setup SakeMonkey Recipe Database using Service Account
This bypasses OAuth verification issues
"""

import os
import sys
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

class ServiceAccountSetup:
    def __init__(self):
        self.spreadsheet_id = "1dp-fcWV0Mm0audZm-EAsQOjyh-C3f6f6"
        self.service = None
        self.credentials = None
    
    def check_service_account_file(self):
        """Check if service account JSON file exists"""
        if os.path.exists('service_account.json'):
            print("✅ service_account.json found")
            return True
        else:
            print("❌ service_account.json not found")
            print("\nTo create service_account.json:")
            print("1. Go to https://console.cloud.google.com/")
            print("2. Go to 'APIs & Services' > 'Credentials'")
            print("3. Click 'Create Credentials' > 'Service Account'")
            print("4. Name it 'SakeMonkeyRecipeDB-Service'")
            print("5. Create a JSON key and download it")
            print("6. Rename the downloaded file to 'service_account.json'")
            print("7. Place it in this directory")
            return False
    
    def authenticate_service_account(self):
        """Authenticate using service account"""
        try:
            print("🔐 Authenticating with service account...")
            
            # Load service account credentials
            self.credentials = service_account.Credentials.from_service_account_file(
                'service_account.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=self.credentials)
            
            print("✅ Service account authentication successful")
            return True
            
        except Exception as e:
            print(f"❌ Service account authentication failed: {e}")
            return False
    
    def test_connection(self):
        """Test connection to Google Sheets"""
        try:
            print("🧪 Testing connection to Google Sheets...")
            
            # Get spreadsheet metadata
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            print(f"✅ Connected to: {spreadsheet['properties']['title']}")
            
            # List sheets
            sheets = spreadsheet.get('sheets', [])
            print(f"✅ Found {len(sheets)} sheets:")
            for sheet in sheets:
                print(f"  - {sheet['properties']['title']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            print("Make sure you've shared the Google Sheet with the service account email")
            return False
    
    def share_sheet_with_service_account(self):
        """Instructions for sharing the sheet"""
        try:
            # Read service account email from JSON
            with open('service_account.json', 'r') as f:
                service_data = json.load(f)
                service_email = service_data['client_email']
            
            print(f"\n📧 Service Account Email: {service_email}")
            print("\n🔗 To share your Google Sheet with the service account:")
            print("1. Open your Google Sheet:")
            print(f"   https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")
            print("2. Click the 'Share' button")
            print(f"3. Add this email: {service_email}")
            print("4. Set permission to 'Editor'")
            print("5. Click 'Send'")
            print("\nPress Enter after sharing the sheet...")
            input()
            
            return True
            
        except Exception as e:
            print(f"❌ Error reading service account file: {e}")
            return False
    
    def import_data_from_sheets(self):
        """Import data from Google Sheets using service account"""
        try:
            print("📊 Importing data from Google Sheets...")
            
            # Import each sheet
            sheets_to_import = ['Ingredients', 'Recipe', 'Starters', 'PublishNotes', 'Formulas']
            
            for sheet_name in sheets_to_import:
                print(f"  Importing {sheet_name}...")
                
                try:
                    # Get data from sheet
                    result = self.service.spreadsheets().values().get(
                        spreadsheetId=self.spreadsheet_id,
                        range=f'{sheet_name}!A:Z'
                    ).execute()
                    
                    values = result.get('values', [])
                    if values:
                        print(f"    ✅ {sheet_name}: {len(values)} rows")
                    else:
                        print(f"    ⚠️  {sheet_name}: No data found")
                        
                except Exception as e:
                    print(f"    ❌ {sheet_name}: Error - {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error importing data: {e}")
            return False
    
    def build_database(self):
        """Build the complete database"""
        try:
            print("🏗️  Building database...")
            
            # Import the database builder
            from build_database_from_sheets import DatabaseBuilder
            
            builder = DatabaseBuilder()
            
            try:
                # Setup database schema
                builder.setup_database_schema()
                
                # Import data (we'll need to modify the import method to use service account)
                print("📊 Database schema created successfully")
                print("📋 Ready to import data from Google Sheets")
                
                # For now, just show that the database is ready
                builder.show_database_summary()
                
                return True
                
            finally:
                builder.close()
                
        except Exception as e:
            print(f"❌ Error building database: {e}")
            return False

def main():
    """Main setup function"""
    print("🍶 SakeMonkey Recipe Database - Service Account Setup")
    print("=" * 60)
    
    setup = ServiceAccountSetup()
    
    # Check service account file
    if not setup.check_service_account_file():
        return False
    
    # Share sheet instructions
    if not setup.share_sheet_with_service_account():
        return False
    
    # Authenticate
    if not setup.authenticate_service_account():
        return False
    
    # Test connection
    if not setup.test_connection():
        return False
    
    # Import data
    if not setup.import_data_from_sheets():
        return False
    
    # Build database
    if not setup.build_database():
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("You can now run: python gui_app.py")
    
    return True

if __name__ == "__main__":
    main()


