"""
Script to backup database content to Google Sheets
Run this to sync all database data to your Google Sheet
"""
import sys
from google_sheets_sync import sync_to_google_sheets

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backup_to_sheets.py <SPREADSHEET_ID>")
        print("\nTo find your Google Sheets Spreadsheet ID:")
        print("1. Open your Google Sheet")
        print("2. Look at the URL: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit")
        print("3. Copy the SPREADSHEET_ID part")
        sys.exit(1)
    
    spreadsheet_id = sys.argv[1]
    print(f"Backing up database to Google Sheets (ID: {spreadsheet_id})...")
    sync_to_google_sheets(spreadsheet_id)
    print("\nBackup completed!")

