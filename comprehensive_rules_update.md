# Comprehensive Database Rules Update

## All Table Rules Based on User Input:

### 1. **Recipe Table Rules:**
- **start_date**: Date a batch starts (DATE type)
- **pouch_date**: When batch was completed and pouched (DATE type)
- **batchID**: Unifying reference key across tables for the batch
- **batch**: Increment on batch made (INTEGER)
- **style**: Categorical limited to ('pure', 'rustic', 'rustic_experimental')
- **kake/koji**: Must be ingredientID with rice type from ingredient table
- **yeast**: Must be ingredientID with yeast type from ingredient table
- **starter**: Must refer to StarterBatch from starters table
- **water_type**: Categorical ingredientID from ingredient table (water category)
- **total_kake_g**: Running total of kake rice added across all additions
- **total_koji_g**: Running total of koji rice added across all additions
- **total_water_mL**: Running total of water in mL added across all additions
- **ferment_temp_C**: Temperature in C that ferment was conducted at
- **addition1_notes/addition2_notes/addition3_notes**: Notes for each addition
- **ferment_finish_gravity**: Measured specific gravity at end of ferment
- **ferment_finish_brix**: Measured percent brix at end of ferment
- **final_measured_temp_C**: Measured temperature at which final measurements took place
- **final_measured_gravity**: Measured float value for specific gravity of final product
- **final_measured_brix**: Measured float value for percent brix
- **final_gravity**: Calculated formula using temperature correction
- **abv**: Calculated formula using brix and gravity
- **smv**: Calculated formula using gravity
- **final_water_addition_mL**: How much water was added before final measurements
- **clarified**: Boolean if process was undertaken
- **pasteurized**: Boolean if process was undertaken
- **pasteurization_notes**: Notes if pasteurized process taken
- **finishing_additions**: Final addition notes

### 2. **Ingredients Table Rules:**
- **ID**: In-database reference for that ingredient
- **Type**: What type of ingredient (category)
- **Rice**: Can be used for making koji OR kake (not separate categories)
- **acc_date**: Accession date into the database as a defined ingredient

### 3. **Starters Table Rules:**
- **Date**: Date the starter was created (DATE type)
- **StarterBatch**: In-database ID for starting conditions of a batch
- **BatchID**: Unifying ID for a batch across tables
- **Amt_Kake**: How much kake rice was added (grams) - contributes to total_kake_g
- **Amt_Koji**: How much koji rice was added (grams) - contributes to total_koji_g
- **Amt_water**: How much liquid was added (mL)
- **water_type**: Categorical ingredientID from ingredient table (water category)
- **Kake/Koji**: ingredientID for rice type from ingredient table
- **yeast**: ingredientID for yeast type from ingredient table
- **lactic_acid**: Grams of lactic acid solution added
- **MgSO4**: Grams of MgSO4 added
- **KCl**: Grams of KCl added
- **temp_C**: Temperature in C at which starter began its ferment

### 4. **PublishNotes Table Rules:**
- **BatchID**: Unifying reference key across tables for the batch
- **Pouch_Date**: When batch was completed and pouched (DATE type)
- **Style**: Categorical limited to ('pure', 'rustic', 'rustic_experimental')
- **Water**: Categorical ingredientID from ingredient table (water category)
- **ABV**: ABV_% value from recipe table
- **SMV**: SMV value from recipe table
- **Batch_Size_L**: total_water_mL from recipe table plus final water additions (converted to L)
- **Rice**: Description of kake_rice used in the batch from ingredient table
- **Description**: Tasting notes and brief sake recipe description

### 5. **Formulas Table Rules:**
- **calibrated_temp_c**: Calibrated hydrometer temperature (default 20°C)
- **measured_temp_c**: Measured temperature
- **measured_sg**: Measured specific gravity
- **measured_brix**: Measured %Brix
- **corrected_gravity**: Live calculated using temperature correction
- **calculated_abv**: Live calculated ABV% from corrected gravity and brix
- **calculated_smv**: Live calculated SMV from corrected gravity
- **created_at**: Timestamp of calculation

## Key Relationships:
- Rice ingredients can be used for both koji and kake
- Water types are categorical ingredients (spring, well, distilled)
- Starters contribute to recipe totals (Amt_Kake → total_kake_g, Amt_Koji → total_koji_g)
- PublishNotes reference recipe data for public display
- Formulas provide live calculations for brewing decisions

## Database Schema Updates:
- Added all missing fields to Recipe table
- Updated foreign key relationships
- Added CHECK constraints for categorical fields
- Updated Formulas table for live calculator functionality
- Enhanced PublishNotes table with proper relationships

## GUI Updates:
- Expanded Recipe form with all new fields
- Added process checkboxes (clarified, pasteurized)
- Updated all CRUD operations to handle new fields
- Enhanced form validation and clearing
- Improved ingredient loading logic for proper categorization


