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

Run the database interface:
```bash
python database_interface.py
```
