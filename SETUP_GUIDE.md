# SakeMonkey Recipe Database - Setup Guide

## Quick Start

### 1. Update Conda Environment

The SakeMonkey conda environment already exists. To update it with the latest packages:

Open **Miniconda PowerShell** and run:

```powershell
cd Database\SakeMonkeyRecipeDB
.\update_environment.ps1
```

Or manually:
```powershell
conda env update -n SakeMonkey -f environment.yml --prune
conda activate SakeMonkey
python setup.py --skip-env
```

**Note:** The workspace is configured to use the SakeMonkey conda environment. VS Code/Cursor should automatically detect it. If not, you can:
1. Select the Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter" → Choose "SakeMonkey"
2. Or run `python find_conda_env.py` to get the exact path and update `.vscode/settings.json`

### 2. Sync Initial Data from Google Sheets

After the environment is set up, sync your master Google Sheet data:

```powershell
python sync_initial_data.py <SPREADSHEET_ID>
```

**To find your Google Sheets Spreadsheet ID:**
1. Open your Google Sheet
2. Look at the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
3. Copy the `SPREADSHEET_ID` part (the long string between `/d/` and `/edit`)

### 3. Run the GUI Application

```powershell
python gui_app.py
```

## Project Structure

- `models.py` - SQLModel database models (Recipe, Ingredient, Starter, PublishNote)
- `database.py` - Database initialization and session management
- `google_sheets_sync.py` - Google Sheets synchronization functionality
- `formulas.py` - Brewing calculation formulas (gravity correction, ABV%, SMV, dilution)
- `gui_app.py` - Main GUI application with tabs for all tables and formulas
- `setup.py` - Database initialization script
- `sync_initial_data.py` - Script to sync initial data from Google Sheets

## Database Schema

### Ingredients Table
- `ID` - Primary key, ingredient identifier
- `ingredient_type` - Type of ingredient (rice, kake_rice, koji_rice, yeast, water)
- `acc_date` - Accession date
- `source` - Source of ingredient
- `description` - Description

### Recipe Table
Main batch tracking with all brewing parameters, measurements, and calculated values.

### Starters Table
Yeast starter management with ingredient amounts and conditions.

### PublishNotes Table
Public-facing product information derived from recipe data.

## GUI Features

The GUI application provides:

1. **Ingredients Tab** - View and manage ingredients
2. **Recipes Tab** - View and manage recipe batches
3. **Starters Tab** - View and manage yeast starters
4. **Publish Notes Tab** - View and manage publish notes
5. **Formulas Tab** - Live calculators for:
   - Gravity correction (temperature-based)
   - ABV% and SMV calculations
   - Dilution adjustments (Pure and Mixer profiles)

## Google Sheets Sync

The application can sync data from a master Google Sheet. The sheet should have the following worksheets:
- `Ingredients`
- `Recipe`
- `Starters`
- `PublishNotes`

Use the "Sync from Google Sheets" option in the File menu, or run `sync_initial_data.py` from the command line.

## Formulas

### Gravity Correction
Corrects specific gravity measurements based on temperature using the formula from rules.txt.

### ABV% Calculation
Calculates alcohol by volume from brix and corrected gravity.

### SMV Calculation
Calculates Sake Meter Value from corrected gravity.

### Dilution Calculator
Calculates water additions needed to reach target profiles:
- **Pure**: 11% brix, 1.005 SG
- **Mixer**: 12% brix, 0.995 SG

## Troubleshooting

### Conda Environment Issues
If the conda environment creation fails:
1. Make sure you're using Miniconda PowerShell
2. Check that `environment.yml` is in the correct location
3. Try creating manually: `conda env create -f environment.yml`

### Google Sheets Sync Issues

**Error: "[400]: This operation is not supported for this document"**

This error means the service account doesn't have access to your Google Sheet. To fix:

1. Open your Google Sheet in a web browser
2. Click the **"Share"** button (top right)
3. In the "Add people and groups" field, enter the service account email:
   ```
   807090979892-compute@developer.gserviceaccount.com
   ```
4. Set the permission to **"Viewer"** (read-only is sufficient for syncing)
5. **Uncheck** "Notify people" (service accounts don't have email addresses)
6. Click **"Share"**
7. Try running the sync script again

**Other common issues:**
1. Ensure `service_account.json` is in the `Database/SakeMonkeyRecipeDB/` directory
2. Check that the spreadsheet ID is correct (from the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`)
3. Ensure worksheet names match exactly: `Ingredients`, `Recipe`, `Starters`, `PublishNotes`

### Database Issues
If the database doesn't initialize:
1. Check file permissions in the `Database/SakeMonkeyRecipeDB/` directory
2. Run `python setup.py --skip-env` to reinitialize
3. Check that SQLite is working: `python -c "import sqlite3; print('OK')"`

## Next Steps

After setup:
1. Sync your initial data from Google Sheets
2. Explore the GUI interface
3. Use the Formulas tab to calculate brewing parameters
4. Add/edit data through the GUI tabs

