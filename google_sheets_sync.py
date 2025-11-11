"""
Google Sheets synchronization functionality
Syncs data from master Google Sheet to local SQLite database
"""
from typing import Optional  # <-- add this
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlmodel import Session, select
from models import Ingredient, Recipe, Starter, PublishNote
from database import get_session, init_database
from datetime import datetime, date
import os
import json

# ---- AUTH / CONFIG ----------------------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def resolve_creds_path(explicit_path: Optional[str] = None) -> str:
    """
    Resolve the service account JSON path with a predictable priority:
      1) explicit_path if provided and exists
      2) GOOGLE_APPLICATION_CREDENTIALS env var if set and exists
      3) ./service_account.json adjacent to this file (dev-only fallback)
    """
    if explicit_path and os.path.exists(explicit_path):
        return explicit_path

    envp = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if envp and os.path.exists(envp):
        return envp

    local = os.path.join(os.path.dirname(__file__), "service_account.json")
    if os.path.exists(local):
        return local

    raise FileNotFoundError(
        "Service account JSON not found. Provide creds_path, or set "
        "GOOGLE_APPLICATION_CREDENTIALS, or place service_account.json next to this file."
    )

def get_service_account_email(creds_path: Optional[str] = None) -> str:
    """Get the service account email from the credentials file (for helpful error messages)."""
    try:
        path = resolve_creds_path(creds_path)
        with open(path, "r") as f:
            return json.load(f).get("client_email", "unknown@unknown")
    except Exception:
        return "unknown@unknown"

def get_google_sheets_service(creds_path: Optional[str] = None):
    """Get authenticated Google Sheets API service using a robust path resolution."""
    path = resolve_creds_path(creds_path)
    creds = Credentials.from_service_account_file(path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)

def verify_spreadsheet_access(spreadsheet_id: str, creds_path: Optional[str] = None):
    """Verify service account can access the spreadsheet and give clear 400/403/404 hints."""
    service = get_google_sheets_service(creds_path)
    try:
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id, includeGridData=False
        ).execute()
        spreadsheet_title = spreadsheet.get("properties", {}).get("title", "Unknown")
        print(f"✓ Access verified. Spreadsheet: '{spreadsheet_title}'")
        return True
    except HttpError as error:
        sa_email = get_service_account_email(creds_path)
        status = getattr(error, "status_code", None)
        if not status and hasattr(error, "resp") and hasattr(error.resp, "status"):
            status = error.resp.status
        msg = str(error).lower()
        if status == 404:
            raise Exception(
                "Spreadsheet not found (404). Verify the spreadsheet ID.\n"
                f"Spreadsheet ID: {spreadsheet_id}\n"
                "Tip: Use the string between /d/ and /edit in the Sheet URL."
            )
        elif status == 400 and "not supported for this document" in msg:
            raise Exception(
                "The provided ID is not a Google Sheet (400: not supported for this document).\n"
                "Open the URL in a browser and confirm it’s a Sheet (not a Doc/Slide/Folder)."
            )
        elif status == 403:
            raise Exception(
                f"\n{'='*70}\n"
                f"PERMISSION DENIED (403): Service account lacks access to the spreadsheet.\n"
                f"{'='*70}\n\n"
                f"Share the Sheet with this service account email as **Editor**:\n"
                f"  {sa_email}\n\n"
                "If using Google Workspace, ensure external sharing is allowed or own the Sheet "
                "with the same Workspace as the service account.\n"
                f"Spreadsheet ID: {spreadsheet_id}\n"
            )
        else:
            raise Exception(f"Error verifying access: {error}")

# ---- SHEETS READ/WRITE ------------------------------------------------------------

def get_sheet_data(service, spreadsheet_id: str, sheet_name: str):
    """Get all data from a specific sheet as a list of dictionaries"""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:ZZ"
        ).execute()
        values = result.get('values', [])
        if not values:
            return []
        headers = [h.strip() if isinstance(h, str) else str(h) for h in values[0]]
        records = []
        for row in values[1:]:
            row_padded = row + [''] * (len(headers) - len(row))
            records.append(dict(zip(headers, row_padded)))
        return records
    except HttpError as error:
        status = getattr(error, "status_code", None)
        if not status and hasattr(error, "resp") and hasattr(error.resp, "status"):
            status = error.resp.status
        if status == 400 and "not supported for this document" in str(error).lower():
            raise Exception(
                f"\n{'='*70}\n"
                f"Invalid target: the ID is not a Google Sheet (400: not supported for this document).\n"
                f"{'='*70}\n\n"
                f"Check the ID and ensure it points to a Google Sheet.\n"
                f"Spreadsheet ID: {spreadsheet_id}\n"
                f"Sheet: {sheet_name}\n"
            )
        raise Exception(f"Error accessing sheet '{sheet_name}': {error}")

def format_value_for_sheet(value):
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    if isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    return str(value)

def write_sheet_data(service, spreadsheet_id: str, sheet_name: str, headers: list, rows: list):
    """Write data to a Google Sheet, replacing all existing content"""
    try:
        values = [headers] + [[format_value_for_sheet(row.get(h, '')) for h in headers] for row in rows]
        range_name = f"{sheet_name}!A1"
        body = {'values': values}
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        # best-effort clear beyond written rows
        if values:
            sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = sheet_metadata.get('sheets', [])
            sheet_info = next((s['properties'] for s in sheets if s['properties']['title'] == sheet_name), None)
            if sheet_info:
                max_rows = sheet_info.get('gridProperties', {}).get('rowCount', 0)
                if max_rows > len(values):
                    clear_range = f"{sheet_name}!A{len(values) + 1}:ZZ{max_rows}"
                    service.spreadsheets().values().clear(
                        spreadsheetId=spreadsheet_id,
                        range=clear_range
                    ).execute()
        return result
    except HttpError as error:
        raise Exception(f"Error writing to sheet '{sheet_name}': {error}")

# ---- PARSERS (unchanged) ----------------------------------------------------------

def parse_date(date_str):
    if not date_str or date_str == "":
        return None
    try:
        if isinstance(date_str, str):
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
        return None
    except Exception:
        return None

def parse_float(value):
    if not value or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def parse_int(value):
    if not value or value == "":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None

def parse_bool(value):
    if not value or value == "":
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ['true', 'yes', '1', 'x', 'checked']
    return bool(value)

# ---- SYNC FUNCTIONS (unchanged) ---------------------------------------------------
# ---- SYNC (Sheets -> DB) ----------------------------------------------------------

def sync_ingredients_from_sheet(service, spreadsheet_id: str, session: Session):
    """Sync ingredients from Google Sheet"""
    try:
        records = get_sheet_data(service, spreadsheet_id, "Ingredients")
        for record in records:
            ingredient = Ingredient(
                ID=parse_int(record.get('ID')) or parse_int(record.get('ingredientID')),
                ingredient_type=record.get('ingredient_type') or record.get('type', ''),
                acc_date=parse_date(record.get('acc_date')),
                source=record.get('source'),
                description=record.get('description')
            )
            existing = session.get(Ingredient, ingredient.ID)
            if existing:
                for key, value in ingredient.dict(exclude={'ID'}).items():
                    if value is not None:
                        setattr(existing, key, value)
            else:
                session.add(ingredient)
        session.commit()
        print(f"Synced {len(records)} ingredients")
    except Exception as e:
        print(f"Error syncing ingredients: {e}")
        session.rollback()

def sync_starters_from_sheet(service, spreadsheet_id: str, session: Session):
    """Sync starters from Google Sheet"""
    try:
        records = get_sheet_data(service, spreadsheet_id, "Starters")
        for record in records:
            starter = Starter(
                StarterBatch=parse_int(record.get('StarterBatch')),
                Date=parse_date(record.get('Date')),
                BatchID=record.get('BatchID'),
                Amt_Kake=parse_float(record.get('Amt_Kake')),
                Amt_Koji=parse_float(record.get('Amt_Koji')),
                Amt_water=parse_float(record.get('Amt_water')),
                water_type=parse_int(record.get('water_type')),
                Kake=parse_int(record.get('Kake')),
                Koji=parse_int(record.get('Koji')),
                yeast=parse_int(record.get('yeast')),
                lactic_acid=parse_float(record.get('lactic_acid')),
                MgSO4=parse_float(record.get('MgSO4')),
                KCl=parse_float(record.get('KCl')),
                temp_C=parse_float(record.get('temp_C'))
            )
            existing = session.get(Starter, starter.StarterBatch)
            if existing:
                for key, value in starter.dict(exclude={'StarterBatch'}).items():
                    if value is not None:
                        setattr(existing, key, value)
            else:
                session.add(starter)
        session.commit()
        print(f"Synced {len(records)} starters")
    except Exception as e:
        print(f"Error syncing starters: {e}")
        session.rollback()

def sync_recipes_from_sheet(service, spreadsheet_id: str, session: Session):
    """Sync recipes from Google Sheet"""
    try:
        records = get_sheet_data(service, spreadsheet_id, "Recipe")
        for record in records:
            recipe = Recipe(
                batchID=record.get('batchID'),
                start_date=parse_date(record.get('start_date')),
                pouch_date=parse_date(record.get('pouch_date')),
                batch=parse_int(record.get('batch')),
                style=record.get('style'),
                kake=parse_int(record.get('kake')),
                koji=parse_int(record.get('koji')),
                yeast=parse_int(record.get('yeast')),
                starter=parse_int(record.get('starter')),
                water_type=parse_int(record.get('water_type')),
                total_kake_g=parse_float(record.get('total_kake_g')),
                total_koji_g=parse_float(record.get('total_koji_g')),
                total_water_mL=parse_float(record.get('total_water_mL')),
                ferment_temp_C=parse_float(record.get('ferment_temp_C')),
                Addition1_Notes=record.get('Addition1_Notes'),
                Addition2_Notes=record.get('Addition2_Notes'),
                Addition3_Notes=record.get('Addition3_Notes'),
                ferment_finish_gravity=parse_float(record.get('ferment_finish_gravity')),
                ferment_finish_brix=parse_float(record.get('ferment_finish_brix')),
                final_measured_temp_C=parse_float(record.get('final_measured_temp_C')),
                final_measured_gravity=parse_float(record.get('final_measured_gravity')),
                final_measured_Brix_pct=parse_float(record.get('final_measured_Brix_%')),
                final_gravity=parse_float(record.get('final_gravity')),
                ABV_pct=parse_float(record.get('ABV_%')),
                SMV=parse_float(record.get('SMV')),
                final_water_addition_mL=parse_float(record.get('final_water_addition_mL')),
                clarified=parse_bool(record.get('clarified')),
                pasteurized=parse_bool(record.get('pasteurized')),
                pasteurization_notes=record.get('pasteurization_notes'),
                finishing_additions=record.get('finishing_additions')
            )
            existing = session.get(Recipe, recipe.batchID)
            if existing:
                for key, value in recipe.dict(exclude={'batchID'}).items():
                    if value is not None:
                        setattr(existing, key, value)
            else:
                session.add(recipe)
        session.commit()
        print(f"Synced {len(records)} recipes")
    except Exception as e:
        print(f"Error syncing recipes: {e}")
        session.rollback()

def sync_publishnotes_from_sheet(service, spreadsheet_id: str, session: Session):
    """Sync publish notes from Google Sheet"""
    try:
        records = get_sheet_data(service, spreadsheet_id, "PublishNotes")
        for record in records:
            publish_note = PublishNote(
                BatchID=record.get('BatchID'),
                Pouch_Date=parse_date(record.get('Pouch_Date')),
                Style=record.get('Style'),
                Water=parse_int(record.get('Water')),
                ABV=parse_float(record.get('ABV')),
                SMV=parse_float(record.get('SMV')),
                Batch_Size_L=parse_float(record.get('Batch_Size_L')),
                Rice=record.get('Rice'),
                Description=record.get('Description')
            )
            existing = session.get(PublishNote, publish_note.BatchID)
            if existing:
                for key, value in publish_note.dict(exclude={'BatchID'}).items():
                    if value is not None:
                        setattr(existing, key, value)
            else:
                session.add(publish_note)
        session.commit()
        print(f"Synced {len(records)} publish notes")
    except Exception as e:
        print(f"Error syncing publish notes: {e}")
        session.rollback()

# ---- SYNC (DB -> Sheets) ----------------------------------------------------------

def sync_ingredients_to_sheet(service, spreadsheet_id: str, session: Session):
    """Sync ingredients from database to Google Sheet, adding new records that don't exist in sheet"""
    try:
        # Get all ingredients from database
        statement = select(Ingredient)
        db_ingredients = session.exec(statement).all()
        
        # Get existing sheet data
        sheet_records = get_sheet_data(service, spreadsheet_id, "Ingredients")
        existing_ids = {parse_int(r.get('ID')) or parse_int(r.get('ingredientID')) for r in sheet_records if r.get('ID') or r.get('ingredientID')}
        
        # Find new ingredients (in DB but not in sheet)
        new_ingredients = [ing for ing in db_ingredients if ing.ID and ing.ID not in existing_ids]
        
        if new_ingredients:
            # Prepare headers based on model fields
            headers = ['ID', 'ingredient_type', 'acc_date', 'source', 'description']
            
            # Convert new ingredients to dict format
            new_rows = []
            for ing in new_ingredients:
                row = {
                    'ID': ing.ID,
                    'ingredient_type': ing.ingredient_type or '',
                    'acc_date': format_value_for_sheet(ing.acc_date),
                    'source': ing.source or '',
                    'description': ing.description or ''
                }
                new_rows.append(row)
            
            # Append new rows to sheet
            if sheet_records:
                # Sheet has data, append after existing rows
                next_row = len(sheet_records) + 2  # +1 for header, +1 for next row
                range_name = f"Ingredients!A{next_row}"
                body = {'values': [[format_value_for_sheet(row.get(h, '')) for h in headers] for row in new_rows]}
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
            else:
                # Sheet is empty, write headers and data
                write_sheet_data(service, spreadsheet_id, "Ingredients", headers, new_rows)
            
            print(f"Added {len(new_ingredients)} new ingredients to sheet")
        else:
            print("No new ingredients to add to sheet")
    except Exception as e:
        print(f"Error syncing ingredients to sheet: {e}")
        raise

def sync_starters_to_sheet(service, spreadsheet_id: str, session: Session):
    """Sync starters from database to Google Sheet, adding new records that don't exist in sheet"""
    try:
        # Get all starters from database
        statement = select(Starter)
        db_starters = session.exec(statement).all()
        
        # Get existing sheet data
        sheet_records = get_sheet_data(service, spreadsheet_id, "Starters")
        existing_batches = {parse_int(r.get('StarterBatch')) for r in sheet_records if r.get('StarterBatch')}
        
        # Find new starters (in DB but not in sheet)
        new_starters = [st for st in db_starters if st.StarterBatch and st.StarterBatch not in existing_batches]
        
        if new_starters:
            # Prepare headers based on model fields
            headers = ['StarterBatch', 'Date', 'BatchID', 'Amt_Kake', 'Amt_Koji', 'Amt_water', 
                      'water_type', 'Kake', 'Koji', 'yeast', 'lactic_acid', 'MgSO4', 'KCl', 'temp_C']
            
            # Convert new starters to dict format
            new_rows = []
            for st in new_starters:
                row = {
                    'StarterBatch': st.StarterBatch,
                    'Date': format_value_for_sheet(st.Date),
                    'BatchID': st.BatchID or '',
                    'Amt_Kake': format_value_for_sheet(st.Amt_Kake),
                    'Amt_Koji': format_value_for_sheet(st.Amt_Koji),
                    'Amt_water': format_value_for_sheet(st.Amt_water),
                    'water_type': format_value_for_sheet(st.water_type),
                    'Kake': format_value_for_sheet(st.Kake),
                    'Koji': format_value_for_sheet(st.Koji),
                    'yeast': format_value_for_sheet(st.yeast),
                    'lactic_acid': format_value_for_sheet(st.lactic_acid),
                    'MgSO4': format_value_for_sheet(st.MgSO4),
                    'KCl': format_value_for_sheet(st.KCl),
                    'temp_C': format_value_for_sheet(st.temp_C)
                }
                new_rows.append(row)
            
            # Append new rows to sheet
            if sheet_records:
                # Sheet has data, append after existing rows
                next_row = len(sheet_records) + 2  # +1 for header, +1 for next row
                range_name = f"Starters!A{next_row}"
                body = {'values': [[format_value_for_sheet(row.get(h, '')) for h in headers] for row in new_rows]}
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
            else:
                # Sheet is empty, write headers and data
                write_sheet_data(service, spreadsheet_id, "Starters", headers, new_rows)
            
            print(f"Added {len(new_starters)} new starters to sheet")
        else:
            print("No new starters to add to sheet")
    except Exception as e:
        print(f"Error syncing starters to sheet: {e}")
        raise

def sync_recipes_to_sheet(service, spreadsheet_id: str, session: Session):
    """Sync recipes from database to Google Sheet, adding new records that don't exist in sheet"""
    try:
        # Get all recipes from database
        statement = select(Recipe)
        db_recipes = session.exec(statement).all()
        
        # Get existing sheet data
        sheet_records = get_sheet_data(service, spreadsheet_id, "Recipe")
        existing_batch_ids = {r.get('batchID') for r in sheet_records if r.get('batchID')}
        
        # Find new recipes (in DB but not in sheet)
        new_recipes = [r for r in db_recipes if r.batchID and r.batchID not in existing_batch_ids]
        
        if new_recipes:
            # Prepare headers based on model fields
            headers = ['batchID', 'start_date', 'pouch_date', 'batch', 'style', 'kake', 'koji', 'yeast', 
                      'starter', 'water_type', 'total_kake_g', 'total_koji_g', 'total_water_mL', 
                      'ferment_temp_C', 'Addition1_Notes', 'Addition2_Notes', 'Addition3_Notes',
                      'ferment_finish_gravity', 'ferment_finish_brix', 'final_measured_temp_C',
                      'final_measured_gravity', 'final_measured_Brix_%', 'final_gravity', 'ABV_%', 
                      'SMV', 'final_water_addition_mL', 'clarified', 'pasteurized', 
                      'pasteurization_notes', 'finishing_additions']
            
            # Convert new recipes to dict format
            new_rows = []
            for recipe in new_recipes:
                row = {
                    'batchID': recipe.batchID or '',
                    'start_date': format_value_for_sheet(recipe.start_date),
                    'pouch_date': format_value_for_sheet(recipe.pouch_date),
                    'batch': format_value_for_sheet(recipe.batch),
                    'style': recipe.style or '',
                    'kake': format_value_for_sheet(recipe.kake),
                    'koji': format_value_for_sheet(recipe.koji),
                    'yeast': format_value_for_sheet(recipe.yeast),
                    'starter': format_value_for_sheet(recipe.starter),
                    'water_type': format_value_for_sheet(recipe.water_type),
                    'total_kake_g': format_value_for_sheet(recipe.total_kake_g),
                    'total_koji_g': format_value_for_sheet(recipe.total_koji_g),
                    'total_water_mL': format_value_for_sheet(recipe.total_water_mL),
                    'ferment_temp_C': format_value_for_sheet(recipe.ferment_temp_C),
                    'Addition1_Notes': recipe.Addition1_Notes or '',
                    'Addition2_Notes': recipe.Addition2_Notes or '',
                    'Addition3_Notes': recipe.Addition3_Notes or '',
                    'ferment_finish_gravity': format_value_for_sheet(recipe.ferment_finish_gravity),
                    'ferment_finish_brix': format_value_for_sheet(recipe.ferment_finish_brix),
                    'final_measured_temp_C': format_value_for_sheet(recipe.final_measured_temp_C),
                    'final_measured_gravity': format_value_for_sheet(recipe.final_measured_gravity),
                    'final_measured_Brix_%': format_value_for_sheet(recipe.final_measured_Brix_pct),
                    'final_gravity': format_value_for_sheet(recipe.final_gravity),
                    'ABV_%': format_value_for_sheet(recipe.ABV_pct),
                    'SMV': format_value_for_sheet(recipe.SMV),
                    'final_water_addition_mL': format_value_for_sheet(recipe.final_water_addition_mL),
                    'clarified': format_value_for_sheet(recipe.clarified),
                    'pasteurized': format_value_for_sheet(recipe.pasteurized),
                    'pasteurization_notes': recipe.pasteurization_notes or '',
                    'finishing_additions': recipe.finishing_additions or ''
                }
                new_rows.append(row)
            
            # Append new rows to sheet
            if sheet_records:
                # Sheet has data, append after existing rows
                next_row = len(sheet_records) + 2  # +1 for header, +1 for next row
                range_name = f"Recipe!A{next_row}"
                body = {'values': [[format_value_for_sheet(row.get(h, '')) for h in headers] for row in new_rows]}
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
            else:
                # Sheet is empty, write headers and data
                write_sheet_data(service, spreadsheet_id, "Recipe", headers, new_rows)
            
            print(f"Added {len(new_recipes)} new recipes to sheet")
        else:
            print("No new recipes to add to sheet")
    except Exception as e:
        print(f"Error syncing recipes to sheet: {e}")
        raise

def sync_publishnotes_to_sheet(service, spreadsheet_id: str, session: Session):
    """Sync publish notes from database to Google Sheet, adding new records that don't exist in sheet"""
    try:
        # Get all publish notes from database
        statement = select(PublishNote)
        db_notes = session.exec(statement).all()
        
        # Get existing sheet data
        sheet_records = get_sheet_data(service, spreadsheet_id, "PublishNotes")
        existing_batch_ids = {r.get('BatchID') for r in sheet_records if r.get('BatchID')}
        
        # Find new publish notes (in DB but not in sheet)
        new_notes = [n for n in db_notes if n.BatchID and n.BatchID not in existing_batch_ids]
        
        if new_notes:
            # Prepare headers based on model fields
            headers = ['BatchID', 'Pouch_Date', 'Style', 'Water', 'ABV', 'SMV', 'Batch_Size_L', 'Rice', 'Description']
            
            # Convert new notes to dict format
            new_rows = []
            for note in new_notes:
                row = {
                    'BatchID': note.BatchID or '',
                    'Pouch_Date': format_value_for_sheet(note.Pouch_Date),
                    'Style': note.Style or '',
                    'Water': format_value_for_sheet(note.Water),
                    'ABV': format_value_for_sheet(note.ABV),
                    'SMV': format_value_for_sheet(note.SMV),
                    'Batch_Size_L': format_value_for_sheet(note.Batch_Size_L),
                    'Rice': note.Rice or '',
                    'Description': note.Description or ''
                }
                new_rows.append(row)
            
            # Append new rows to sheet
            if sheet_records:
                # Sheet has data, append after existing rows
                next_row = len(sheet_records) + 2  # +1 for header, +1 for next row
                range_name = f"PublishNotes!A{next_row}"
                body = {'values': [[format_value_for_sheet(row.get(h, '')) for h in headers] for row in new_rows]}
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
            else:
                # Sheet is empty, write headers and data
                write_sheet_data(service, spreadsheet_id, "PublishNotes", headers, new_rows)
            
            print(f"Added {len(new_notes)} new publish notes to sheet")
        else:
            print("No new publish notes to add to sheet")
    except Exception as e:
        print(f"Error syncing publish notes to sheet: {e}")
        raise

# ---- TOP-LEVEL ENTRY POINTS (signatures fixed) -----------------------------------

def sync_from_google_sheets(spreadsheet_id: str, creds_path: Optional[str] = None):
    print("Initializing database...")
    init_database()
    print("Connecting to Google Sheets...")
    print(f"Verifying access to spreadsheet: {spreadsheet_id}")
    verify_spreadsheet_access(spreadsheet_id, creds_path)
    service = get_google_sheets_service(creds_path)
    session = get_session()
    try:
        print("Syncing data from Google Sheets...")
        sync_ingredients_from_sheet(service, spreadsheet_id, session)
        sync_starters_from_sheet(service, spreadsheet_id, session)
        sync_recipes_from_sheet(service, spreadsheet_id, session)
        sync_publishnotes_from_sheet(service, spreadsheet_id, session)
        print("Sync completed successfully!")
    except Exception as e:
        print(f"Error during sync: {e}")
        session.rollback()
    finally:
        session.close()

def sync_to_google_sheets(spreadsheet_id: str, creds_path: Optional[str] = None):
    print("Connecting to Google Sheets...")
    print(f"Verifying access to spreadsheet: {spreadsheet_id}")
    verify_spreadsheet_access(spreadsheet_id, creds_path)
    service = get_google_sheets_service(creds_path)
    session = get_session()
    try:
        print("Syncing data to Google Sheets (backup)...")
        sync_ingredients_to_sheet(service, spreadsheet_id, session)
        sync_starters_to_sheet(service, spreadsheet_id, session)
        sync_recipes_to_sheet(service, spreadsheet_id, session)
        sync_publishnotes_to_sheet(service, spreadsheet_id, session)
        print("Backup to Google Sheets completed successfully!")
    except Exception as e:
        print(f"Error during backup: {e}")
        raise
    finally:
        session.close()
