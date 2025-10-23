#!/usr/bin/env python3
"""
Google Sheets synchronization for SakeMonkey Recipe Database
Handles authentication and data sync with Google Sheets
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Sheets API scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class GoogleSheetsSync:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        """
        Initialize Google Sheets sync
        
        Args:
            credentials_file: Path to Google API credentials JSON file
            token_file: Path to store/load OAuth token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.spreadsheet_id = None
        
    def authenticate(self):
        """Authenticate with Google Sheets API"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        "Please download credentials.json from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('sheets', 'v4', credentials=creds)
        return True
    
    def create_spreadsheet(self, title="SakeMonkey Recipe Database"):
        """Create a new Google Spreadsheet"""
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        spreadsheet_body = {
            'properties': {
                'title': title
            },
            'sheets': [
                {'properties': {'title': 'Ingredients'}},
                {'properties': {'title': 'Recipe'}},
                {'properties': {'title': 'Starters'}},
                {'properties': {'title': 'PublishNotes'}},
                {'properties': {'title': 'Formulas'}}
            ]
        }
        
        try:
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()
            
            self.spreadsheet_id = spreadsheet['spreadsheetId']
            print(f"Created spreadsheet: {spreadsheet['spreadsheetUrl']}")
            return self.spreadsheet_id
            
        except HttpError as error:
            print(f"Error creating spreadsheet: {error}")
            return None
    
    def set_spreadsheet_id(self, spreadsheet_id):
        """Set the spreadsheet ID to work with"""
        self.spreadsheet_id = spreadsheet_id
    
    def export_to_sheets(self, db_path='sake_recipe_db.sqlite'):
        """Export SQLite database to Google Sheets"""
        if not self.service or not self.spreadsheet_id:
            raise Exception("Not authenticated or no spreadsheet ID set")
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            # Export each table
            tables = {
                'Ingredients': 'ingredients',
                'Recipe': 'recipe', 
                'Starters': 'starters',
                'PublishNotes': 'publish_notes',
                'Formulas': 'formulas'
            }
            
            for sheet_name, table_name in tables.items():
                print(f"Exporting {table_name} to {sheet_name} sheet...")
                
                # Get data from SQLite
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                if not rows:
                    print(f"No data in {table_name} table")
                    continue
                
                # Prepare data for Google Sheets
                headers = [description[0] for description in cursor.description]
                data = [headers]  # Header row
                
                for row in rows:
                    data.append([str(cell) if cell is not None else '' for cell in row])
                
                # Clear existing data and write new data
                range_name = f"{sheet_name}!A:Z"
                
                # Clear the sheet
                self.service.spreadsheets().values().clear(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name
                ).execute()
                
                # Write new data
                body = {'values': data}
                result = self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                print(f"Updated {result.get('updatedCells')} cells in {sheet_name}")
            
            print("Export completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error exporting to sheets: {e}")
            return False
        
        finally:
            conn.close()
    
    def import_from_sheets(self, db_path='sake_recipe_db.sqlite'):
        """Import data from Google Sheets to SQLite database"""
        if not self.service or not self.spreadsheet_id:
            raise Exception("Not authenticated or no spreadsheet ID set")
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            # Import each sheet
            sheets = ['Ingredients', 'Recipe', 'Starters', 'PublishNotes', 'Formulas']
            
            for sheet_name in sheets:
                print(f"Importing {sheet_name} sheet...")
                
                # Get data from Google Sheets
                range_name = f"{sheet_name}!A:Z"
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name
                ).execute()
                
                values = result.get('values', [])
                if not values:
                    print(f"No data in {sheet_name} sheet")
                    continue
                
                # Skip if only header row
                if len(values) <= 1:
                    print(f"Only header row in {sheet_name} sheet")
                    continue
                
                headers = values[0]
                data_rows = values[1:]
                
                # Map to appropriate table
                table_mapping = {
                    'Ingredients': 'ingredients',
                    'Recipe': 'recipe',
                    'Starters': 'starters', 
                    'PublishNotes': 'publish_notes',
                    'Formulas': 'formulas'
                }
                
                table_name = table_mapping.get(sheet_name)
                if not table_name:
                    print(f"No table mapping for {sheet_name}")
                    continue
                
                # Clear existing data
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {table_name}")
                
                # Insert new data
                for row in data_rows:
                    # Pad row with empty strings if needed
                    while len(row) < len(headers):
                        row.append('')
                    
                    # Create placeholders for SQL
                    placeholders = ', '.join(['?' for _ in headers])
                    columns = ', '.join(headers)
                    
                    try:
                        cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", row)
                    except Exception as e:
                        print(f"Error inserting row: {e}")
                        continue
                
                conn.commit()
                print(f"Imported {len(data_rows)} rows to {table_name}")
            
            print("Import completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error importing from sheets: {e}")
            return False
        
        finally:
            conn.close()
    
    def get_spreadsheet_url(self):
        """Get the URL of the current spreadsheet"""
        if self.spreadsheet_id:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
        return None
    
    def list_sheets(self):
        """List all sheets in the current spreadsheet"""
        if not self.service or not self.spreadsheet_id:
            return []
        
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheets = []
            for sheet in spreadsheet.get('sheets', []):
                sheets.append({
                    'title': sheet['properties']['title'],
                    'sheetId': sheet['properties']['sheetId']
                })
            
            return sheets
            
        except HttpError as error:
            print(f"Error listing sheets: {error}")
            return []

def setup_google_credentials():
    """Helper function to guide user through Google API setup"""
    print("=== Google Sheets API Setup ===")
    print("To use Google Sheets sync, you need to:")
    print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
    print("2. Create a new project or select existing one")
    print("3. Enable Google Sheets API")
    print("4. Create credentials (OAuth 2.0 Client ID)")
    print("5. Download the credentials JSON file")
    print("6. Save it as 'credentials.json' in this directory")
    print("\nFor detailed instructions, visit:")
    print("https://developers.google.com/sheets/api/quickstart/python")

def main():
    """Test the Google Sheets sync functionality"""
    sync = GoogleSheetsSync()
    
    try:
        # Authenticate
        print("Authenticating with Google Sheets API...")
        sync.authenticate()
        print("Authentication successful!")
        
        # Create or set spreadsheet
        spreadsheet_id = input("Enter Google Spreadsheet ID (or press Enter to create new): ").strip()
        
        if not spreadsheet_id:
            print("Creating new spreadsheet...")
            spreadsheet_id = sync.create_spreadsheet()
            if spreadsheet_id:
                print(f"Created spreadsheet: {sync.get_spreadsheet_url()}")
        else:
            sync.set_spreadsheet_id(spreadsheet_id)
            print(f"Using spreadsheet: {sync.get_spreadsheet_url()}")
        
        # Test export
        print("\nTesting export to Google Sheets...")
        if sync.export_to_sheets():
            print("Export test successful!")
        else:
            print("Export test failed!")
        
    except Exception as e:
        print(f"Error: {e}")
        setup_google_credentials()

if __name__ == "__main__":
    main()
