#!/usr/bin/env python3
"""
Quick setup for your existing Google Sheet
"""

from google_sheets_config import set_spreadsheet_id
from google_sheets_sync import GoogleSheetsSync

def setup_your_sheet():
    """Setup your existing Google Sheet"""
    
    # Your Google Sheet ID from the URL
    spreadsheet_id = "1dp-fcWV0Mm0audZm-EAsQOjyh-C3f6f6"
    
    print("=== Setting up your Google Sheet ===")
    print(f"Google Sheet ID: {spreadsheet_id}")
    print(f"Google Sheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    
    # Set the spreadsheet ID in configuration
    set_spreadsheet_id(spreadsheet_id)
    print("✓ Spreadsheet ID configured")
    
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
                
                # Check sheet structure
                is_valid, message = sync.check_sheet_structure()
                if is_valid:
                    print(f"✓ {message}")
                else:
                    print(f"⚠ {message}")
                    print("The system will create missing sheets during the first sync.")
                
                print(f"\n✓ Configuration complete!")
                print(f"Google Sheet URL: {sync.get_spreadsheet_url()}")
                print("\nYou can now use the GUI to sync your database with this Google Sheet.")
                return True
            else:
                print("⚠ Connected but no sheets found")
                return False
        else:
            print("✗ Authentication failed")
            print("You may need to set up Google API credentials first.")
            print("Run: python setup_google_sheets.py")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        if "credentials" in str(e).lower():
            print("You need to set up Google API credentials first.")
            print("Run: python setup_google_sheets.py")
        return False

def main():
    """Main function"""
    if setup_your_sheet():
        print("\n=== Setup Complete! ===")
        print("Your Google Sheet is now configured for sync.")
        print("Run 'python gui_app.py' to use the sync functionality.")
    else:
        print("\n=== Setup Failed ===")
        print("Please check the error messages above.")
        print("You may need to set up Google API credentials first:")
        print("Run: python setup_google_sheets.py")

if __name__ == "__main__":
    main()
