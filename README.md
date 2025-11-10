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

The database is built from an Excel file with the following sheets:
- `Ingredients`: ingredientID, ingredient_type, acc_date, source, description
- `Recipe`: start_date, pouch_date, batchID, batch, style, kake, koji, yeast, starter, water_type
- `Starters`: Date, StarterBatch, BatchID, Amt_Kake, Amt_Koji, Amt_water, water_type, Kake, Koji, yeast
- `PublishNotes`: BatchID, Pouch_Date, Style, Water, ABV, SMV, Batch_Size_L, Rice, Description
- `Formulas`: Brewing calculations and measurement formulas

## Setup

### Option 1: Conda Environment (Recommended for Development)
1. Create and activate conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate SakeMonkey
   ```

2. Initialize the database:
   ```bash
   python setup_database.py
   ```

3. Import data from Excel:
   ```bash
   python import_excel_data.py
   ```

### Option 2: Docker Containerization (Recommended for Production)
1. Setup Docker environment:
   ```bash
   python setup_docker.py
   ```

2. Start the application:
   ```bash
   docker-compose up
   ```

### Option 3: Manual Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Initialize the database:
   ```bash
   python setup_database.py
   ```

3. Import data from Excel:
   ```bash
   python import_excel_data.py
   ```

## Usage

### Command Line Interface
Run the database interface:
```bash
python database_interface.py
```

### Graphical User Interface
Run the GUI application:
```bash
python gui_app.py
```
or
```bash
python run_gui.py
```

### GUI Features
The GUI provides an intuitive interface for:
- **Ingredients Tab**: Add and manage ingredients (yeast, rice, koji, etc.)
- **Recipes Tab**: Create and manage sake recipes with batch information
- **Starters Tab**: Track yeast starter development and measurements
- **Publish Notes Tab**: Record final product details (ABV, SMV, etc.)
- **View Data Tab**: Database statistics and data overview

### Quick Start
1. Run `python gui_app.py` to open the GUI
2. Navigate between tabs to add different types of data
3. Use the "Load Data" buttons to refresh dropdown lists
4. View statistics in the "View Data" tab

## Google Sheets Integration

### Setup Google Sheets Sync
1. Install Google API dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up Google Sheets API credentials:
   ```bash
   python setup_google_sheets.py
   ```

3. Follow the setup wizard to:
   - Configure Google Cloud Console credentials
   - Create or link a Google Spreadsheet
   - Test the sync functionality

### Using Google Sheets Sync
- **Export to Google Sheets**: Upload your local database to Google Sheets
- **Import from Google Sheets**: Download data from Google Sheets to local database
- **Automatic Backup**: Keep your data synchronized across devices
- **Collaborative Editing**: Share your spreadsheet with team members

### Google Sheets Tab Features
- **Authentication**: Connect to your Google account
- **Configuration**: Set your spreadsheet ID
- **Sync Operations**: Export/import data with progress tracking
- **Status Monitoring**: Real-time sync status and error reporting

## Docker Usage

### Quick Start with Docker
```bash
# Setup Docker environment
python setup_docker.py

# Start the application
docker-compose up

# Run in background
docker-compose up -d

# Stop the application
docker-compose down
```

### Docker Commands
```bash
# Run GUI application
docker-compose run --rm sakemonkey-db python gui_app.py

# Run CLI interface
docker-compose run --rm sakemonkey-db python database_interface.py

# Initialize database
docker-compose run --rm sakemonkey-db python setup_database.py

# Import Excel data
docker-compose run --rm sakemonkey-db python import_excel_data.py

# Create backup
docker-compose run --rm backup
```

### Data Persistence
- **Database**: `./data/sake_recipe_db.sqlite`
- **Credentials**: `./credentials/`
- **Logs**: `./logs/`
- **Backups**: `./backups/`
