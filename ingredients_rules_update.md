# Ingredients Table Rules Update

## Corrected Rules Based on User Input:

### Ingredients Table:
- **ID**: In-database reference for that ingredient
- **Type**: What type of ingredient (category)
- **Rice**: Can be used for making koji OR kake (not separate categories)
- **acc_date**: Accession date into the database as a defined ingredient

## Changes Made to GUI:

### 1. Ingredient Type Options:
**Before (Incorrect):**
- 'yeast', 'koji_rice', 'kake_rice', 'rice', 'nutrientMix', 'water', 'other'

**After (Correct):**
- 'yeast', 'rice', 'nutrientMix', 'water', 'other'

### 2. Form Labels:
**Before:** "Access Date"
**After:** "Accession Date"

### 3. Ingredient Loading Logic:
**Before:** Separate categories for koji_rice and kake_rice
**After:** Rice ingredients can be used for both koji and kake

### 4. Recipe Form:
- Kake Rice dropdown: Shows all rice ingredients
- Koji Rice dropdown: Shows all rice ingredients (same list)
- Yeast dropdown: Shows only yeast ingredients

### 5. Starter Form:
- Kake Rice dropdown: Shows all rice ingredients
- Koji Rice dropdown: Shows all rice ingredients (same list)
- Yeast dropdown: Shows only yeast ingredients

## Key Insight:
Rice is a single ingredient type that can be used for multiple purposes (koji or kake), rather than having separate categories for each use case.


