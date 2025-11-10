# SakeMonkey Recipe Database Setup Guide

## 🍶 Complete Database Setup from Google Sheets

This guide will help you build a complete SQLite database using your Google Sheet data and the table rules from `rules.txt`.

## 📋 Prerequisites

1. **SakeMonkey conda environment activated**
2. **Google Sheets API credentials** (credentials.json)
3. **Your Google Sheet** with the data

## 🚀 Quick Start

### Step 1: Activate Environment
```bash
conda activate SakeMonkey
cd Database/SakeMonkeyRecipeDB
```

### Step 2: Install Dependencies
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Step 3: Setup Google Sheets Integration
```bash
python setup_google_sheets_integration.py
```

### Step 4: Build Database from Google Sheets
```bash
python build_database_from_sheets.py
```

### Step 5: Launch GUI
```bash
python gui_app.py
```

## 🔧 Detailed Setup

### 1. Google Sheets API Setup

#### Get Google API Credentials:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API
4. Go to "APIs & Services" > "Credentials"
5. Click "Create Credentials" > "OAuth 2.0 Client ID"
6. Choose "Desktop application"
7. Download the JSON file
8. Rename it to `credentials.json`
9. Place it in `Database/SakeMonkeyRecipeDB/`

#### Your Google Sheet:
- **URL**: https://docs.google.com/spreadsheets/d/1dp-fcWV0Mm0audZm-EAsQOjyh-C3f6f6
- **ID**: `1dp-fcWV0Mm0audZm-EAsQOjyh-C3f6f6`
- **Sheets**: Ingredients, Recipe, Starters, PublishNotes, Formulas

### 2. Database Schema

The database is built according to your `rules.txt` specifications:

#### **Ingredients Table:**
- `ingredientID` (TEXT, PRIMARY KEY)
- `ingredient_type` (TEXT) - yeast, rice, nutrientMix, water, other
- `acc_date` (DATE) - accession date
- `source` (TEXT)
- `description` (TEXT)

#### **Recipe Table:**
- `batchID` (TEXT, UNIQUE) - unifying reference key
- `batch` (INTEGER) - increment on batch made
- `style` (TEXT) - pure, rustic, rustic_experimental
- `start_date` (DATE) - batch start date
- `pouch_date` (DATE) - batch completion date
- `kake`, `koji`, `yeast` (TEXT) - ingredient references
- `starter` (TEXT) - starter batch reference
- `water_type` (TEXT) - water ingredient reference
- `total_kake_g`, `total_koji_g`, `total_water_mL` (REAL) - running totals
- `ferment_temp_C` (REAL) - fermentation temperature
- `addition1_notes`, `addition2_notes`, `addition3_notes` (TEXT)
- `ferment_finish_gravity`, `ferment_finish_brix` (REAL)
- `final_measured_temp_C`, `final_measured_gravity`, `final_measured_brix` (REAL)
- `final_gravity`, `abv`, `smv` (REAL) - calculated values
- `clarified`, `pasteurized` (BOOLEAN) - process flags
- `pasteurization_notes`, `finishing_additions` (TEXT)

#### **Starters Table:**
- `date` (DATE) - starter creation date
- `starter_batch` (TEXT) - in-database ID
- `batchID` (TEXT) - unifying reference key
- `amt_kake`, `amt_koji`, `amt_water` (REAL) - amounts in grams/mL
- `water_type`, `kake`, `koji`, `yeast` (TEXT) - ingredient references
- `lactic_acid`, `MgSO4`, `KCl` (REAL) - chemistry additions
- `temp_C` (REAL) - fermentation temperature

#### **PublishNotes Table:**
- `batchID` (TEXT) - unifying reference key
- `pouch_date` (DATE) - completion date
- `style` (TEXT) - recipe style
- `water` (TEXT) - water ingredient reference
- `abv`, `smv` (REAL) - from recipe table
- `batch_size_l` (REAL) - total volume in liters
- `rice` (TEXT) - rice description
- `description` (TEXT) - tasting notes

#### **Formulas Table:**
- `calibrated_temp_c` (REAL) - hydrometer calibration temp (default 20°C)
- `measured_temp_c`, `measured_sg`, `measured_brix` (REAL) - input values
- `corrected_gravity`, `calculated_abv`, `calculated_smv` (REAL) - calculated values
- `created_at` (TIMESTAMP) - calculation timestamp

### 3. Data Import Process

The `build_database_from_sheets.py` script:

1. **Creates database schema** based on rules.txt
2. **Authenticates** with Google Sheets API
3. **Imports data** from each sheet:
   - Ingredients → ingredients table
   - Recipe → recipe table
   - Starters → starters table
   - PublishNotes → publish_notes table
   - Formulas → formulas table
4. **Validates data** and handles missing values
5. **Shows summary** of imported data

### 4. GUI Features

Once the database is built, the GUI provides:

- **Ingredients Tab**: Manage ingredient database
- **Recipes Tab**: Complete recipe management with full view
- **Starters Tab**: Starter management with chemistry tracking
- **Publish Notes Tab**: Public-facing recipe information
- **Live Calculator Tab**: Real-time brewing calculations
- **View Data Tab**: Database overview and queries
- **Google Sheets Sync Tab**: Bidirectional sync with Google Sheets

## 🔄 Data Synchronization

### Export to Google Sheets:
- Upload local database changes to Google Sheets
- Maintains data integrity across platforms

### Import from Google Sheets:
- Download changes from Google Sheets to local database
- Handles new records and updates

### Automatic Backup:
- Keep data synchronized across devices
- Collaborative editing support

## 🧪 Testing

### Test Database Setup:
```bash
python test_gui_fixes.py
```

### Test Google Sheets Integration:
```bash
python setup_google_sheets_integration.py
```

### Test Full Build:
```bash
python build_database_from_sheets.py
```

## 📊 Database Summary

After successful setup, you'll have:

- **Complete SQLite database** with all tables and relationships
- **Data imported** from your Google Sheet
- **Full GUI interface** for database management
- **Live calculator** for brewing calculations
- **Google Sheets sync** for backup and collaboration
- **Docker containerization** ready for deployment

## 🎯 Next Steps

1. **Run the setup** following the quick start guide
2. **Test the GUI** to ensure everything works
3. **Add sample data** to test all functionality
4. **Set up Google Sheets sync** for ongoing data management
5. **Deploy with Docker** when ready for production

## 🆘 Troubleshooting

### Common Issues:

1. **"No item with that key" error**: Database schema mismatch - run `python setup_database.py`
2. **Google Sheets authentication failed**: Check credentials.json file
3. **Import errors**: Verify Google Sheet structure matches expected format
4. **GUI not starting**: Ensure all dependencies are installed in SakeMonkey environment

### Getting Help:

- Check the logs for specific error messages
- Verify your Google Sheet has the correct structure
- Ensure all required packages are installed
- Test each component individually

## 🎉 Success!

Once everything is set up, you'll have a complete sake brewing database management system that:

- ✅ Follows your exact table rules from rules.txt
- ✅ Imports data from your Google Sheet
- ✅ Provides a full GUI interface
- ✅ Includes live brewing calculations
- ✅ Supports Google Sheets synchronization
- ✅ Is ready for Docker containerization



