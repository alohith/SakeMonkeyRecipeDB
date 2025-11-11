"""
Script to sync initial data from Google Sheets
Run this after setting up the environment to import master data
"""
import sys
import os
from google_sheets_sync import sync_from_google_sheets, resolve_creds_path

USAGE = (
    "Usage:\n"
    "  python sync_initial_data.py <SPREADSHEET_ID> [CREDS_PATH]\n\n"
    "To find your Google Sheets Spreadsheet ID:\n"
    "1. Open your Google Sheet\n"
    "2. URL looks like: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit\n"
    "3. Copy the SPREADSHEET_ID part\n\n"
    "If CREDS_PATH is omitted, the script will try:\n"
    "  - $GOOGLE_APPLICATION_CREDENTIALS\n"
    "  - ./service_account.json (next to google_sheets_sync.py)\n"
)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)

    spreadsheet_id = sys.argv[1]
    creds_path = sys.argv[2] if len(sys.argv) >= 3 else None

    # Resolve (and validate) the credentials path now for clear errors
    try:
        resolved = resolve_creds_path(creds_path)
    except FileNotFoundError as e:
        print(str(e))
        sys.exit(1)

    print(f"Syncing data from Google Sheets (ID: {spreadsheet_id})...")
    print(f"Using service account JSON: {resolved}")
    sync_from_google_sheets(spreadsheet_id, creds_path=resolved)
    print("\nInitial data sync completed!")
