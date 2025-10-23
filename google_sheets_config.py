#!/usr/bin/env python3
"""
Configuration for Google Sheets integration
"""

# Google Sheets configuration
GOOGLE_SHEETS_CONFIG = {
    # Default spreadsheet ID (set this to your Google Sheet ID)
    'spreadsheet_id': None,  # Replace with your actual spreadsheet ID
    
    # Sheet names mapping
    'sheet_names': {
        'ingredients': 'Ingredients',
        'recipe': 'Recipe', 
        'starters': 'Starters',
        'publish_notes': 'PublishNotes',
        'formulas': 'Formulas'
    },
    
    # Auto-sync settings
    'auto_sync': False,  # Set to True for automatic sync
    'sync_interval_minutes': 30,  # Sync interval in minutes
    
    # Backup settings
    'backup_before_sync': True,  # Create backup before syncing
    'max_backups': 5,  # Maximum number of backups to keep
}

# Instructions for setup
SETUP_INSTRUCTIONS = """
Google Sheets API Setup Instructions:

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project or select an existing one
3. Enable the Google Sheets API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Download the JSON file
   - Rename it to 'credentials.json' and place in this directory
5. Set your spreadsheet ID in google_sheets_config.py
6. Run the sync to authenticate

Your spreadsheet should have these sheets:
- Ingredients
- Recipe  
- Starters
- PublishNotes
- Formulas
"""

def get_spreadsheet_id():
    """Get the configured spreadsheet ID"""
    return GOOGLE_SHEETS_CONFIG['spreadsheet_id']

def set_spreadsheet_id(spreadsheet_id):
    """Set the spreadsheet ID"""
    GOOGLE_SHEETS_CONFIG['spreadsheet_id'] = spreadsheet_id

def get_sheet_name(table_name):
    """Get the Google Sheet name for a database table"""
    return GOOGLE_SHEETS_CONFIG['sheet_names'].get(table_name, table_name)

def is_auto_sync_enabled():
    """Check if auto-sync is enabled"""
    return GOOGLE_SHEETS_CONFIG['auto_sync']

def get_sync_interval():
    """Get sync interval in minutes"""
    return GOOGLE_SHEETS_CONFIG['sync_interval_minutes']
