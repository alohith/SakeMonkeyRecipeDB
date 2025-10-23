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
