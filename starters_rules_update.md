# Starters Table Rules Update

## Corrected Rules Based on User Input:

### Starters Table:
- **Date**: Date the starter was created (DATE type)
- **StarterBatch**: In-database ID for starting conditions of a batch
- **BatchID**: Unifying ID for a batch across tables (the batch this starter is going into)
- **Amt_Kake**: How much kake rice was added (grams) - contributes to total_kake_g in recipe table
- **Amt_Koji**: How much koji rice was added (grams) - contributes to total_koji_g in recipe table
- **Amt_water**: How much liquid was added (ml)
- **water_type**: Categorical ingredientID from ingredient table of category 'water' (spring, well, distilled)
- **Kake**: ingredientID for rice type from ingredient table
- **Koji**: ingredientID for rice type from ingredient table
- **yeast**: ingredientID for yeast type from ingredient table
- **lactic_acid**: Grams of lactic acid solution added
- **MgSO4**: Grams of MgSO4 added
- **KCl**: Grams of KCl added
- **temp_C**: Temperature in Celsius at which the starter began its ferment

## Changes Made:

### 1. Database Schema Updates:
- Added missing fields: `lactic_acid`, `MgSO4`, `KCl`, `temp_C`
- Updated foreign key for `water_type` to reference ingredients table
- Maintained proper relationships between tables

### 2. GUI Form Updates:
- Added new input fields for chemistry components:
  - Lactic Acid (g)
  - MgSO4 (g) 
  - KCl (g)
  - Temperature (°C)
- Updated form layout to accommodate new fields
- Fixed button positioning after adding new fields

### 3. Data Handling Updates:
- Updated `add_starter()` method to include new fields
- Updated `clear_starter_form()` to clear new fields
- Updated `load_starter_data()` to display temperature in treeview
- Updated ingredient loading to properly populate water type dropdown

### 4. Key Relationships:
- **Amt_Kake** and **Amt_Koji** contribute to recipe totals
- **water_type** references ingredients table (water category)
- **Kake**, **Koji**, **yeast** reference ingredients table
- **BatchID** links to recipe table for batch tracking

## Important Notes:
- Rice ingredients can be used for both koji and kake (same dropdown options)
- Water types are categorical ingredients (spring, well, distilled)
- Chemistry fields (lactic_acid, MgSO4, KCl) are optional but important for fermentation tracking
- Temperature tracking is crucial for fermentation monitoring
