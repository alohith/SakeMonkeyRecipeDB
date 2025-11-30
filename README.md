# SakeMonkey Recipe Database

A comprehensive database system for managing sake brewing recipes, ingredients, and batch tracking.

## Project Structure

This project contains:
- **Ingredients**: Track different types of ingredients (yeast, koji rice, kake rice, etc.)
- **Recipes**: Main recipe records with batch information
- **Starters**: Yeast starter management
- **Publish Notes**: Final product information
- **Formulas**: Brewing calculations and measurements

## Database Schema

The database uses SQLite with the following tables:
- `Ingredients`: ingredientID, ingredient_type, acc_date, source, description
- `Recipe`: start_date, pouch_date, batchID, batch, style, kake, koji, yeast, starter, water_type, and calculated fields (ABV%, SMV, etc.)
- `Starters`: Date, StarterBatch, BatchID, Amt_Kake, Amt_Koji, Amt_water, water_type, Kake, Koji, yeast, lactic_acid, MgSO4, KCl, temp_C
- `PublishNotes`: BatchID, Pouch_Date, Style, Water, ABV, SMV, Batch_Size_L, Rice, Description

## Setup

### Conda Environment (Recommended)

1. Create and activate conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate SakeMonkey
   ```

2. Initialize the database:
   ```bash
   python setup.py --skip-env
   ```
   Or use the PowerShell script:
   ```powershell
   .\setup_conda.ps1
   ```

3. Sync initial data from Google Sheets (optional):
   ```bash
   python sync_initial_data.py <SPREADSHEET_ID>
   ```

### Manual Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Initialize the database:
   ```bash
   python setup.py --skip-env
   ```

## Usage

### Graphical User Interface

Run the GUI application:
```bash
python gui_app.py
```

### GUI Features

The GUI provides an intuitive interface with the following tabs:

- **Ingredients Tab**: View, add, and manage ingredients (yeast, rice, koji, etc.)
- **Recipes Tab**: View, add, and manage sake recipes with batch information
- **Starters Tab**: View, add, and manage yeast starter development and measurements
- **Publish Notes Tab**: View and manage final product details (ABV, SMV, etc.)
- **Formulas Tab**: Live calculators for:
  - Gravity correction (temperature-based)
  - ABV% and SMV calculations
  - Dilution adjustments (Pure and Mixer target profiles)
- **Validate Tab**: Validate database records against business rules
- **Google Sync Tab**: Sync data to/from Google Sheets with progress tracking

### Quick Start

1. Run `python gui_app.py` to open the GUI
2. Navigate between tabs to view and manage data
3. Use the "Load Data" buttons to refresh data grids
4. Use the Formulas tab for brewing calculations
5. Use File menu → "Sync from Google Sheets" or "Sync to Google Sheets" for backup/restore

## Google Sheets Integration

### Setup

1. Place your `service_account.json` credentials file in the project directory
2. The default spreadsheet ID is configured in `gui_app.py` (can be changed in the sync dialog)

### Using Google Sheets Sync

- **Sync from Google Sheets**: Import data from your master Google Sheet to the local database
  - Use File menu → "Sync from Google Sheets" in the GUI
  - Or run: `python sync_initial_data.py <SPREADSHEET_ID>`
- **Sync to Google Sheets**: Export/backup your local database to Google Sheets
  - Use File menu → "Sync to Google Sheets" in the GUI
  - Or use the Google Sync tab for more control

### Google Sheets Features

- **Bidirectional Sync**: Import from and export to Google Sheets
- **Data Validation**: Validates data against rules document during sync
- **Type Preservation**: Numbers are written as numeric values (not strings) for proper formula support
- **Style Conversion**: Automatically converts between database format (lowercase) and publish format (capitalized)

## Command Line Interface

A command-line interface is available via `gooey_interface.py` using Gooey for GUI-based CLI operations:

```bash
python gooey_interface.py
```

This provides a GUI wrapper for command-line operations to add/edit ingredients, recipes, starters, and publish notes.

## Formulas

The Formulas tab provides live calculators:

- **Gravity Correction**: Corrects specific gravity measurements based on temperature
- **ABV% Calculation**: Calculates alcohol by volume from brix and corrected gravity
- **SMV Calculation**: Calculates Sake Meter Value from corrected gravity
- **Dilution Calculator**: Calculates water additions needed to reach target profiles:
  - **Pure**: 11% brix, 1.005 SG
  - **Mixer**: 12% brix, 0.995 SG

## TODO

- [ ] **Implement auto-update/auto-populate of PublishNotes page/sheet**
  - Populate data in this table from the corresponding fields of the recipe page/sheet using rules document
  - Currently PublishNotes must be manually populated or synced from Google Sheets (partially implemented to populate upon entry update)

- [ ] **Docker containerization**
  - Create Dockerfile and docker-compose.yml for containerized deployment
  - Setup script for Docker environment



- [ ] **Command Line Interface (CLI)**
  - Text-based CLI interface (currently only Gooey GUI wrapper exists)
  - Direct command-line operations without GUI

- [ ] **Edit functionality improvements**
  - Fix edit function on recipe page
    - Ensure edit popup menu appears correctly following the rules document

- [ ] **Additional features**
  - View Data tab with database statistics and data overview
  - Enhanced error handling and user feedback

