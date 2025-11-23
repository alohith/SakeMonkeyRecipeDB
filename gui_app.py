"""
SakeMonkey Recipe Database GUI Application
Built with wxPython for full database interface
Incorporates functionality from gooey_interface.py per rules.txt
"""
import wx
import wx.adv
import wx.grid
import wx.lib.scrolledpanel as scrolled
import re
from datetime import date, datetime
from sqlmodel import Session, select
from database import get_session, init_database
from models import (
    Ingredient, Recipe, Starter, PublishNote,
    IngredientTypeEnum, StyleEnum
)
from formulas import (
    calculate_final_gravity, calculate_abv, calculate_smv,
    calculate_dilution_adjustment
)
from google_sheets_sync import sync_from_google_sheets, sync_to_google_sheets
import os

# Default Google Sheet ID from rules.txt
DEFAULT_SPREADSHEET_ID = "1wGSiuApdScc-RULpSyecmA_km4J6k9KYOp0rz3nT2mM"

TARGET_PROFILES = {
    "Pure": {"brix": 11.0, "gravity": 1.005},
    "Mixer": {"brix": 12.0, "gravity": 0.995},
}

RECIPE_COLUMN_ORDER = [
    "start_date", "pouch_date", "batchID", "batch", "style", "kake", "koji", "yeast",
    "starter", "water_type", "total_kake_g", "total_koji_g", "total_water_mL",
    "ferment_temp_C", "Addition1_Notes", "Addition2_Notes", "Addition3_Notes",
    "ferment_finish_gravity", "ferment_finish_brix", "final_measured_temp_C",
    "final_measured_gravity", "final_measured_Brix_pct", "final_gravity", "ABV_pct",
    "SMV", "final_water_addition_mL", "clarified", "pasteurized",
    "pasteurization_notes", "finishing_additions"
]

INGREDIENT_COLUMN_ORDER = [
    "ingredientID", "ingredient_type", "acc_date", "source", "description"
]

STARTER_COLUMN_ORDER = [
    "Date", "StarterBatch", "BatchID", "Amt_Kake", "Amt_Koji", "Amt_water",
    "water_type", "Kake", "Koji", "yeast", "lactic_acid", "MgSO4", "KCl", "temp_C"
]

PUBLISHNOTE_COLUMN_ORDER = [
    "BatchID", "Pouch_Date", "Style", "Water", "ABV", "SMV",
    "Batch_Size_L", "Rice", "Description"
]

BRIX_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%?\s*(?:brix|\xb0brix)", re.IGNORECASE)


def order_columns(columns, desired_order):
    """Return columns ordered according to desired_order, preserving extras at the end"""
    if not desired_order:
        return columns
    ordered = [col for col in desired_order if col in columns]
    ordered.extend([col for col in columns if col not in ordered])
    return ordered


def extract_brix_value(text):
    """Extract a numeric Brix value from free-form text"""
    if not text:
        return None
    match = BRIX_PATTERN.search(text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def describe_ingredient(ingredient: Ingredient) -> str:
    """Format ingredient display"""
    type_part = f"({ingredient.ingredient_type})"
    if ingredient.ingredientID:
        primary_name = ingredient.ingredientID
        if ingredient.description:
            return f"{primary_name} {type_part} - {ingredient.description}"
        else:
            return f"{primary_name} {type_part}"
    if ingredient.source:
        if ingredient.description:
            return f"{ingredient.source} {type_part} - {ingredient.description}"
        else:
            return f"{ingredient.source} {type_part}"
    if ingredient.description:
        return f"{ingredient.description} {type_part}"
    return f"ingredientID {ingredient.ingredientID} {type_part}"


def format_starter_code(value) -> str:
    """Format starter batch code for display"""
    if value is None:
        return "s??"
    value_str = str(value).strip()
    if value_str.lower().startswith('s'):
        return value_str
    try:
        numeric_str = value_str.lstrip('sS')
        numeric_value = int(numeric_str)
        return f"s{numeric_value}"
    except (ValueError, TypeError):
        if not value_str.lower().startswith('s'):
            return f"s{value_str}"
        return value_str


def describe_starter(starter: Starter) -> str:
    """Format starter display"""
    code = format_starter_code(starter.StarterBatch)
    batch_label = starter.BatchID or "unassigned"
    date_label = starter.Date.isoformat() if isinstance(starter.Date, date) else "no date"
    return f"{code} | BatchID {batch_label} | {date_label}"


def get_next_starter_batch(session) -> str:
    """Get the next starter batch ID"""
    result = session.exec(select(Starter.StarterBatch).order_by(Starter.StarterBatch.desc())).first()
    if not result:
        return "s1"
    try:
        result_str = str(result).strip()
        if result_str.lower().startswith('s'):
            numeric_str = result_str.lstrip('sS')
            try:
                numeric_value = int(numeric_str)
                return f"s{numeric_value + 1}"
            except ValueError:
                pass
        numeric_value = int(result)
        return f"s{numeric_value + 1}"
    except (ValueError, TypeError):
        return "s1"


def create_shubo_starter(session, batch_id: str, start_date_value: date,
                         kake_id: str, koji_id: str, yeast_id: str, water_id: str) -> str:
    """Create default Shubo starter: 250g Koji, 250ml Water, .4g Lactic Acid at 6C"""
    starter_batch = get_next_starter_batch(session)
    starter = Starter(
        StarterBatch=starter_batch,
        Date=start_date_value or date.today(),
        BatchID=batch_id,
        Amt_Koji=250.0,
        Amt_water=250.0,
        water_type=water_id,
        Kake=kake_id,
        Koji=koji_id,
        yeast=yeast_id,
        lactic_acid=0.4,
        temp_C=6.0,
    )
    session.add(starter)
    session.commit()
    return starter_batch


class FormulasPanel(scrolled.ScrolledPanel):
    """Panel for formula calculations with live updates"""
    
    def __init__(self, parent, session):
        super().__init__(parent)
        self.session = session
        self.adjustment_brix = 35.0
        self.adjustment_ingredient_items = [None]
        self.init_ui()
    
    def init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(self, label="Sake Brewing Formulas Calculator")
        title_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL | wx.CENTER, 10)
        
        # Gravity Correction Calculator with live updates
        gravity_box = wx.StaticBox(self, label="Gravity Correction Calculator (Live Updates)")
        gravity_sizer = wx.StaticBoxSizer(gravity_box, wx.VERTICAL)
        
        grid = wx.FlexGridSizer(7, 2, 5, 5)
        grid.AddGrowableCol(1, 1)
        
        grid.Add(wx.StaticText(self, label="Calibrated Temp (°C):"), 0, wx.ALL, 5)
        calib_temp_choice = wx.Choice(self, choices=["20", "15.6"])
        calib_temp_choice.SetSelection(0)
        calib_temp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        calib_temp_sizer.Add(calib_temp_choice, 0, wx.ALL, 0)
        calib_temp_sizer.Add(wx.StaticText(self, label=" or Custom:"), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.custom_calib_temp = wx.TextCtrl(self, size=(80, -1))
        calib_temp_sizer.Add(self.custom_calib_temp, 0, wx.ALL, 0)
        self.calibrated_temp_choice = calib_temp_choice
        grid.Add(calib_temp_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        grid.Add(wx.StaticText(self, label="Measured Temp (°C):"), 0, wx.ALL, 5)
        self.measured_temp = wx.TextCtrl(self)
        self.measured_temp.Bind(wx.EVT_TEXT, self.on_gravity_update)
        grid.Add(self.measured_temp, 0, wx.EXPAND | wx.ALL, 5)
        
        grid.Add(wx.StaticText(self, label="Measured Gravity:"), 0, wx.ALL, 5)
        self.measured_gravity = wx.TextCtrl(self)
        self.measured_gravity.Bind(wx.EVT_TEXT, self.on_gravity_update)
        grid.Add(self.measured_gravity, 0, wx.EXPAND | wx.ALL, 5)
        
        grid.Add(wx.StaticText(self, label="Measured %Brix:"), 0, wx.ALL, 5)
        self.measured_brix = wx.TextCtrl(self)
        self.measured_brix.Bind(wx.EVT_TEXT, self.on_gravity_update)
        grid.Add(self.measured_brix, 0, wx.EXPAND | wx.ALL, 5)
        
        grid.Add(wx.StaticText(self, label="Corrected Gravity:"), 0, wx.ALL, 5)
        self.corrected_gravity = wx.TextCtrl(self, style=wx.TE_READONLY)
        grid.Add(self.corrected_gravity, 0, wx.EXPAND | wx.ALL, 5)
        
        grid.Add(wx.StaticText(self, label="ABV%:"), 0, wx.ALL, 5)
        self.abv_result = wx.TextCtrl(self, style=wx.TE_READONLY)
        grid.Add(self.abv_result, 0, wx.EXPAND | wx.ALL, 5)
        
        grid.Add(wx.StaticText(self, label="SMV:"), 0, wx.ALL, 5)
        self.smv_result = wx.TextCtrl(self, style=wx.TE_READONLY)
        grid.Add(self.smv_result, 0, wx.EXPAND | wx.ALL, 5)
        
        gravity_sizer.Add(grid, 0, wx.ALL, 10)
        main_sizer.Add(gravity_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Target Profile Adjustment Calculator
        target_box = wx.StaticBox(self, label="Target Profile Adjustment Calculator")
        target_sizer = wx.StaticBoxSizer(target_box, wx.VERTICAL)
        
        target_grid = wx.FlexGridSizer(7, 2, 5, 5)
        target_grid.AddGrowableCol(1, 1)
        
        # Batch ID selector
        target_grid.Add(wx.StaticText(self, label="BatchID (optional):"), 0, wx.ALL, 5)
        self.batch_id_choice = wx.ComboBox(self, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.batch_id_choice.Bind(wx.EVT_COMBOBOX, self.on_batch_selected)
        target_grid.Add(self.batch_id_choice, 0, wx.EXPAND | wx.ALL, 5)
        
        target_grid.Add(wx.StaticText(self, label="Current Brix (%):"), 0, wx.ALL, 5)
        self.curr_brix = wx.TextCtrl(self)
        self.curr_brix.Bind(wx.EVT_TEXT, self.on_target_update)
        target_grid.Add(self.curr_brix, 0, wx.EXPAND | wx.ALL, 5)
        
        target_grid.Add(wx.StaticText(self, label="Current Gravity:"), 0, wx.ALL, 5)
        self.curr_gravity = wx.TextCtrl(self)
        self.curr_gravity.Bind(wx.EVT_TEXT, self.on_target_update)
        target_grid.Add(self.curr_gravity, 0, wx.EXPAND | wx.ALL, 5)
        
        target_grid.Add(wx.StaticText(self, label="Current Volume (L):"), 0, wx.ALL, 5)
        self.curr_volume = wx.TextCtrl(self)
        self.curr_volume.Bind(wx.EVT_TEXT, self.on_target_update)
        target_grid.Add(self.curr_volume, 0, wx.EXPAND | wx.ALL, 5)
        
        target_grid.Add(wx.StaticText(self, label="Target Profile:"), 0, wx.ALL, 5)
        self.target_profile = wx.Choice(self, choices=list(TARGET_PROFILES.keys()))
        self.target_profile.SetSelection(0)
        self.target_profile.Bind(wx.EVT_CHOICE, self.on_target_update)
        target_grid.Add(self.target_profile, 0, wx.EXPAND | wx.ALL, 5)
        
        target_grid.Add(wx.StaticText(self, label="Adjustment Ingredient:"), 0, wx.ALL, 5)
        self.adjustment_ingredient = wx.ComboBox(self, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.adjustment_ingredient.Bind(wx.EVT_COMBOBOX, self.on_adjustment_selected)
        target_grid.Add(self.adjustment_ingredient, 0, wx.EXPAND | wx.ALL, 5)
        
        target_grid.Add(wx.StaticText(self, label="Volume to Add (L):"), 0, wx.ALL, 5)
        self.volume_to_add = wx.TextCtrl(self, style=wx.TE_READONLY)
        target_grid.Add(self.volume_to_add, 0, wx.EXPAND | wx.ALL, 5)
        
        target_sizer.Add(target_grid, 0, wx.ALL, 10)
        main_sizer.Add(target_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
        self.SetupScrolling()
        self.load_batch_ids()
        self.load_adjustment_ingredients()
    
    def load_batch_ids(self):
        """Load batch IDs from database"""
        try:
            recipes = self.session.exec(select(Recipe.batchID).where(Recipe.batchID.isnot(None))).all()
            batch_ids = [""] + [str(bid) for bid in recipes if bid]
            self.batch_id_choice.SetItems(batch_ids)
        except Exception:
            pass
    
    def load_adjustment_ingredients(self):
        """Load adjustment ingredients (35% Brix amazake)"""
        self.adjustment_ingredient_items = [None]
        try:
            ingredients = self.session.exec(
                select(Ingredient).where(Ingredient.ingredient_type.in_([
                    IngredientTypeEnum.RICE.value,
                    IngredientTypeEnum.KAKI_RICE.value,
                    IngredientTypeEnum.KOJI_RICE.value
                ]))
            ).all()
            choices = [""]
            for ingredient in ingredients:
                choices.append(describe_ingredient(ingredient))
                self.adjustment_ingredient_items.append(ingredient)
            self.adjustment_ingredient.SetItems(choices)
            self.adjustment_ingredient.SetSelection(0)
            self.adjustment_brix = 35.0
        except Exception:
            self.adjustment_ingredient_items = [None]
            self.adjustment_ingredient.SetItems([""])
            self.adjustment_ingredient.SetSelection(0)
            self.adjustment_brix = 35.0

    def get_selected_adjustment_ingredient(self):
        """Return the currently selected adjustment ingredient"""
        selection = self.adjustment_ingredient.GetSelection()
        if selection == wx.NOT_FOUND or selection >= len(self.adjustment_ingredient_items):
            return None
        return self.adjustment_ingredient_items[selection]
    
    def update_adjustment_brix(self):
        """Update the active adjustment Brix value from the selected ingredient"""
        ingredient = self.get_selected_adjustment_ingredient()
        brix = None
        if ingredient and ingredient.description:
            brix = extract_brix_value(ingredient.description)
        self.adjustment_brix = brix if brix is not None else 35.0
    
    def on_adjustment_selected(self, event):
        """Handle adjustment ingredient selection changes"""
        self.update_adjustment_brix()
        self.on_target_update(None)
    
    def on_batch_selected(self, event):
        """Load ferment finish values from selected batch"""
        batch_id = self.batch_id_choice.GetValue()
        if not batch_id:
            return
        try:
            recipe = self.session.get(Recipe, batch_id)
            if recipe:
                if recipe.ferment_finish_brix:
                    self.curr_brix.SetValue(str(recipe.ferment_finish_brix))
                if recipe.ferment_finish_gravity:
                    self.curr_gravity.SetValue(str(recipe.ferment_finish_gravity))
                self.on_target_update(None)
        except Exception:
            pass
    
    def on_gravity_update(self, event):
        """Live update gravity, ABV, and SMV calculations"""
        try:
            mt_str = self.measured_temp.GetValue().strip()
            mg_str = self.measured_gravity.GetValue().strip()
            mb_str = self.measured_brix.GetValue().strip()
            
            # Get calibrated temp
            calib_choice = self.calibrated_temp_choice.GetStringSelection()
            custom_calib = self.custom_calib_temp.GetValue().strip()
            if custom_calib:
                try:
                    ct = float(custom_calib)
                except ValueError:
                    ct = 20.0
            else:
                ct = float(calib_choice) if calib_choice else 20.0
            
            if mt_str and mg_str:
                mt = float(mt_str)
                mg = float(mg_str)
                corrected = calculate_final_gravity(mt, mg, ct)
                if corrected:
                    self.corrected_gravity.SetValue(f"{corrected:.4f}")
                    
                    # Calculate SMV
                    smv = calculate_smv(corrected)
                    if smv:
                        self.smv_result.SetValue(f"{smv:.1f}")
                    
                    # Calculate ABV if brix provided
                    if mb_str:
                        mb = float(mb_str)
                        abv = calculate_abv(mb, corrected)
                        if abv:
                            self.abv_result.SetValue(f"{abv:.1f}")
                    else:
                        self.abv_result.SetValue("")
                else:
                    self.corrected_gravity.SetValue("")
                    self.abv_result.SetValue("")
                    self.smv_result.SetValue("")
            else:
                self.corrected_gravity.SetValue("")
                self.abv_result.SetValue("")
                self.smv_result.SetValue("")
        except (ValueError, TypeError):
            pass
    
    def on_target_update(self, event):
        """Calculate target profile adjustment"""
        try:
            curr_brix_str = self.curr_brix.GetValue().strip()
            curr_gravity_str = self.curr_gravity.GetValue().strip()
            curr_volume_str = self.curr_volume.GetValue().strip()
            
            if curr_brix_str and curr_gravity_str and curr_volume_str:
                curr_brix = float(curr_brix_str)
                curr_gravity = float(curr_gravity_str)
                curr_volume = float(curr_volume_str)
                
                target_name = self.target_profile.GetStringSelection()
                target = TARGET_PROFILES.get(target_name, TARGET_PROFILES["Pure"])
                
                fortifier_brix = self.adjustment_brix if getattr(self, "adjustment_brix", None) else 35.0
                result = calculate_dilution_adjustment(
                    current_brix=curr_brix,
                    current_gravity=curr_gravity,
                    target_brix=target["brix"],
                    target_gravity=target["gravity"],
                    current_volume_L=curr_volume,
                    fortifier_brix=fortifier_brix,
                )
                
                self.volume_to_add.SetValue(f"{result['volume_to_add_L']:.2f} L ({result['addition_type']})")
            else:
                self.volume_to_add.SetValue("")
        except (ValueError, TypeError):
            self.volume_to_add.SetValue("")


class DataGridPanel(wx.Panel):
    """Generic panel for displaying database tables with proper ordering"""
    
    def __init__(self, parent, model_class, session, order_by_field=None):
        super().__init__(parent)
        self.model_class = model_class
        self.session = session
        self.order_by_field = order_by_field
        self.init_ui()
        self.load_data()
    
    def get_desired_column_order(self):
        if self.model_class == Recipe:
            return RECIPE_COLUMN_ORDER
        if self.model_class == Ingredient:
            return INGREDIENT_COLUMN_ORDER
        if self.model_class == Starter:
            return STARTER_COLUMN_ORDER
        if self.model_class == PublishNote:
            return PUBLISHNOTE_COLUMN_ORDER
        return None
    
    def apply_column_order(self, columns):
        return order_columns(columns, self.get_desired_column_order())
    
    def init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Toolbar
        toolbar = wx.BoxSizer(wx.HORIZONTAL)
        refresh_btn = wx.Button(self, label="Refresh")
        refresh_btn.Bind(wx.EVT_BUTTON, lambda e: self.load_data())
        toolbar.Add(refresh_btn, 0, wx.ALL, 5)
        
        add_btn = wx.Button(self, label="Add New")
        add_btn.Bind(wx.EVT_BUTTON, self.on_add)
        toolbar.Add(add_btn, 0, wx.ALL, 5)
        
        edit_btn = wx.Button(self, label="Edit Selected")
        edit_btn.Bind(wx.EVT_BUTTON, self.on_edit)
        toolbar.Add(edit_btn, 0, wx.ALL, 5)
        
        update_btn = wx.Button(self, label="Update Entry")
        update_btn.Bind(wx.EVT_BUTTON, self.on_update_entry)
        toolbar.Add(update_btn, 0, wx.ALL, 5)
        
        delete_btn = wx.Button(self, label="Delete Selected")
        delete_btn.Bind(wx.EVT_BUTTON, self.on_delete)
        toolbar.Add(delete_btn, 0, wx.ALL, 5)
        
        sizer.Add(toolbar, 0, wx.ALL, 5)
        
        # Grid
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(0, 0)
        self.grid.EnableEditing(False)
        self.grid.SetSelectionMode(wx.grid.Grid.SelectRows)
        sizer.Add(self.grid, 1, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(sizer)
    
    def load_data(self):
        """Load data with proper ordering per rules.txt"""
        try:
            statement = select(self.model_class)
            
            # Apply ordering based on model type
            if self.model_class == Recipe:
                statement = statement.order_by(Recipe.batchID)
            elif self.model_class == Starter:
                # Order by BatchID first, then StarterBatch
                statement = statement.order_by(Starter.BatchID, Starter.StarterBatch)
            elif self.model_class == PublishNote:
                statement = statement.order_by(PublishNote.Pouch_Date)
            elif self.model_class == Ingredient:
                statement = statement.order_by(Ingredient.ingredientID)
            
            results = self.session.exec(statement).all()
            
            if not results:
                self.grid.ClearGrid()
                if self.grid.GetNumberRows() > 0:
                    self.grid.DeleteRows(0, self.grid.GetNumberRows())
                if self.grid.GetNumberCols() > 0:
                    self.grid.DeleteCols(0, self.grid.GetNumberCols())
                return
            
            # Get column names from first result
            first = results[0]
            if hasattr(first, "model_dump"):
                columns = list(first.model_dump().keys())
            elif hasattr(first, "dict"):
                columns = list(first.dict().keys())
            else:
                columns = [k for k in first.__dict__.keys() if not k.startswith("_")]
            
            columns = self.apply_column_order(columns)
            
            # Clear and recreate grid
            if self.grid.GetNumberRows() > 0:
                self.grid.DeleteRows(0, self.grid.GetNumberRows())
            if self.grid.GetNumberCols() > 0:
                self.grid.DeleteCols(0, self.grid.GetNumberCols())
            
            self.grid.AppendCols(len(columns))
            self.grid.AppendRows(len(results))
            
            # Set column labels
            for i, col in enumerate(columns):
                self.grid.SetColLabelValue(i, col)
            
            # Populate data
            for row_idx, obj in enumerate(results):
                if hasattr(obj, "model_dump"):
                    data = obj.model_dump()
                elif hasattr(obj, "dict"):
                    data = obj.dict()
                else:
                    data = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
                
                for col_idx, col in enumerate(columns):
                    value = data.get(col, "")
                    if value is None:
                        value = ""
                    elif isinstance(value, (date, datetime)):
                        if isinstance(value, datetime):
                            value = value.date().isoformat()
                        else:
                            value = value.isoformat()
                    elif isinstance(value, bool):
                        value = "Yes" if value else "No"
                    else:
                        value = str(value)
                    self.grid.SetCellValue(row_idx, col_idx, value)
            
            self.grid.AutoSizeColumns()
            self.grid.SetColLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTER)
        except Exception as e:
            wx.MessageBox(f"Error loading data: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
    def get_selected_record(self):
        """Get the selected record"""
        selected = self.grid.GetSelectedRows()
        if selected:
            row = selected[0]
        else:
            row = self.grid.GetGridCursorRow()
            if row is None or row < 0:
                return None
        
        # Get the primary key value from the first column (usually ID)
        pk_value = self.grid.GetCellValue(row, 0)
        if not pk_value:
            return None
        
        # Try to get the record from database
        try:
            return self.session.get(self.model_class, pk_value)
        except Exception:
            return None
    
    def get_record_for_update(self):
        """Return currently selected record or prompt the user to choose one"""
        record = self.get_selected_record()
        if record:
            return record
        return self.prompt_record_selection()
    
    def prompt_record_selection(self):
        """Show a popup menu to choose a record"""
        total_rows = self.grid.GetNumberRows()
        if total_rows <= 0:
            wx.MessageBox("No records available", "Info", wx.OK | wx.ICON_INFORMATION)
            return None
        
        choices = []
        pk_values = []
        col_count = self.grid.GetNumberCols()
        if col_count <= 0:
            wx.MessageBox("No columns available to determine records", "Info", wx.OK | wx.ICON_INFORMATION)
            return None
        
        for row in range(total_rows):
            pk_value = self.grid.GetCellValue(row, 0)
            if not pk_value:
                continue
            preview_cols = []
            for col in range(min(col_count, 3)):
                header = self.grid.GetColLabelValue(col)
                cell_value = self.grid.GetCellValue(row, col)
                preview_cols.append(f"{header}: {cell_value}")
            label = " | ".join(preview_cols)
            choices.append(label)
            pk_values.append(pk_value)
        
        if not choices:
            wx.MessageBox("No valid records found", "Info", wx.OK | wx.ICON_INFORMATION)
            return None
        
        dlg = wx.SingleChoiceDialog(self, "Select a record to update", "Select Record", choices)
        record = None
        if dlg.ShowModal() == wx.ID_OK:
            idx = dlg.GetSelection()
            if 0 <= idx < len(pk_values):
                pk_value = pk_values[idx]
                record = self.session.get(self.model_class, pk_value)
        dlg.Destroy()
        return record
    
    def on_add(self, event):
        """Open add dialog based on model type"""
        if self.model_class == Ingredient:
            dlg = AddIngredientDialog(self, self.session)
        elif self.model_class == Recipe:
            dlg = AddRecipeDialog(self, self.session)
        elif self.model_class == Starter:
            dlg = AddStarterDialog(self, self.session)
        elif self.model_class == PublishNote:
            dlg = AddPublishNoteDialog(self, self.session)
        else:
            wx.MessageBox("Add functionality not implemented for this table", "Info", wx.OK)
            return
        
        if dlg.ShowModal() == wx.ID_OK:
            try:
                data = dlg.GetValue()
                if self.model_class == Ingredient:
                    ingredient = Ingredient(**data)
                    self.session.add(ingredient)
                    self.session.commit()
                elif self.model_class == Recipe:
                    recipe_data = data
                    # Handle starter creation if needed
                    if recipe_data.get("starter") is None:
                        starter_batch = create_shubo_starter(
                            self.session,
                            recipe_data["batchID"],
                            recipe_data["start_date"],
                            recipe_data["kake"],
                            recipe_data["koji"],
                            recipe_data["yeast"],
                            recipe_data["water_type"],
                        )
                        recipe_data["starter"] = starter_batch
                    recipe = Recipe(**recipe_data)
                    self.session.add(recipe)
                    self.session.commit()
                elif self.model_class == Starter:
                    starter_data = data
                    starter_batch_str = starter_data.pop("StarterBatch")
                    if starter_batch_str:
                        starter = Starter(StarterBatch=starter_batch_str, **starter_data)
                        self.session.add(starter)
                        self.session.commit()
                elif self.model_class == PublishNote:
                    publish_data = data
                    # Get recipe to pull ABV, SMV, etc.
                    recipe = self.session.get(Recipe, publish_data["BatchID"])
                    if recipe:
                        publish_data["ABV"] = recipe.ABV_pct
                        publish_data["SMV"] = recipe.SMV
                        # Calculate batch size
                        total_water = (recipe.total_water_mL or 0.0) + (recipe.final_water_addition_mL or 0.0)
                        publish_data["Batch_Size_L"] = round(total_water / 1000.0, 2) if total_water else None
                        # Get rice description
                        if recipe.kake:
                            rice = self.session.get(Ingredient, recipe.kake)
                            if rice:
                                publish_data["Rice"] = f"{rice.ingredientID} - {rice.description or rice.source or ''}"
                    publish = PublishNote(**publish_data)
                    self.session.add(publish)
                    self.session.commit()
                self.load_data()
                wx.MessageBox("Record added successfully", "Success", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"Error adding record: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
                self.session.rollback()
        dlg.Destroy()
    
    def on_edit(self, event):
        """Open edit dialog for selected record"""
        record = self.get_record_for_update()
        if not record:
            return
        
        if self.model_class == Recipe:
            self.open_recipe_update_dialog(record)
        else:
            wx.MessageBox("Edit functionality not fully implemented for this table", "Info", wx.OK)
    
    def on_update_entry(self, event):
        """Launch popup selection and update dialog"""
        record = self.get_record_for_update()
        if not record:
            return
        
        if self.model_class == Recipe:
            self.open_recipe_update_dialog(record)
        else:
            wx.MessageBox("Update functionality currently available for Recipes only.", "Info", wx.OK | wx.ICON_INFORMATION)
    
    def open_recipe_update_dialog(self, record):
        """Open the recipe update dialog and process updates"""
        dlg = UpdateRecipeDialog(self, self.session, record)
        if dlg.ShowModal() == wx.ID_OK:
            try:
                update_data = dlg.GetValue()
                update_type = update_data.pop("update_type")
                
                if update_type in ["addition1", "addition2", "addition3"]:
                    notes_key = f"{update_type.capitalize()}_Notes"
                    setattr(record, notes_key, update_data.get("notes"))
                    # Update totals if kake/koji provided
                    if "kake_g" in update_data:
                        record.total_kake_g = (record.total_kake_g or 0.0) + update_data["kake_g"]
                    if "koji_g" in update_data:
                        record.total_koji_g = (record.total_koji_g or 0.0) + update_data["koji_g"]
                elif update_type == "ferment_finish":
                    if "ferment_finish_gravity" in update_data:
                        record.ferment_finish_gravity = update_data["ferment_finish_gravity"]
                    if "ferment_finish_brix" in update_data:
                        record.ferment_finish_brix = update_data["ferment_finish_brix"]
                elif update_type == "batch_finishing":
                    # Update all finishing fields
                    for key, value in update_data.items():
                        if hasattr(record, key):
                            setattr(record, key, value)
                    
                    # Calculate final gravity, ABV, SMV
                    if update_data.get("final_measured_temp_C") and update_data.get("final_measured_gravity"):
                        calib_temp = float(update_data.get("calibrated_temp", 20.0))
                        record.final_gravity = calculate_final_gravity(
                            update_data["final_measured_temp_C"],
                            update_data["final_measured_gravity"],
                            calib_temp
                        )
                        if update_data.get("final_measured_Brix_pct") and record.final_gravity:
                            record.ABV_pct = calculate_abv(
                                update_data["final_measured_Brix_pct"],
                                record.final_gravity
                            )
                        if record.final_gravity:
                            record.SMV = calculate_smv(record.final_gravity)
                    
                    # Update publish note if publish comment provided
                    if update_data.get("publish_comment"):
                        publish = self.session.get(PublishNote, record.batchID)
                        if not publish:
                            publish = PublishNote(BatchID=record.batchID)
                            self.session.add(publish)
                        publish.Description = update_data["publish_comment"]
                        publish.Pouch_Date = update_data.get("pouch_date")
                        publish.Style = record.style
                        publish.ABV = record.ABV_pct
                        publish.SMV = record.SMV
                
                self.session.add(record)
                self.session.commit()
                self.load_data()
                wx.MessageBox("Record updated successfully", "Success", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"Error updating record: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
                self.session.rollback()
        dlg.Destroy()
    
    def on_delete(self, event):
        """Delete selected record"""
        record = self.get_selected_record()
        if not record:
            wx.MessageBox("Please select a row to delete", "Info", wx.OK)
            return
        
        confirm = wx.MessageBox(
            f"Are you sure you want to delete this record?",
            "Confirm Delete",
            wx.YES_NO | wx.ICON_QUESTION
        )
        
        if confirm == wx.YES:
            try:
                self.session.delete(record)
                self.session.commit()
                self.load_data()
                wx.MessageBox("Record deleted successfully", "Success", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"Error deleting record: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
                self.session.rollback()


# Dialog classes for data entry
class AddIngredientDialog(wx.Dialog):
    """Dialog for adding a new ingredient"""
    
    def __init__(self, parent, session):
        super().__init__(parent, title="Add Ingredient", size=(500, 400))
        self.session = session
        self.init_ui()
    
    def init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Ingredient ID
        sizer.Add(wx.StaticText(self, label="IngredientID:"), 0, wx.ALL, 5)
        self.ingredient_id = wx.TextCtrl(self)
        sizer.Add(self.ingredient_id, 0, wx.EXPAND | wx.ALL, 5)
        
        # Ingredient Type
        sizer.Add(wx.StaticText(self, label="Ingredient Type:"), 0, wx.ALL, 5)
        types = [e.value for e in IngredientTypeEnum]
        self.ingredient_type = wx.Choice(self, choices=types)
        sizer.Add(self.ingredient_type, 0, wx.EXPAND | wx.ALL, 5)
        
        # Accession Date
        sizer.Add(wx.StaticText(self, label="Accession Date:"), 0, wx.ALL, 5)
        date_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.acc_date = wx.adv.DatePickerCtrl(self, style=wx.adv.DP_DROPDOWN)
        self.acc_date.SetValue(wx.DateTime.Today())
        date_sizer.Add(self.acc_date, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(date_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Source
        sizer.Add(wx.StaticText(self, label="Source:"), 0, wx.ALL, 5)
        self.source = wx.TextCtrl(self)
        sizer.Add(self.source, 0, wx.EXPAND | wx.ALL, 5)
        
        # Description
        sizer.Add(wx.StaticText(self, label="Description (up to 300 chars):"), 0, wx.ALL, 5)
        self.description = wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(-1, 100))
        sizer.Add(self.description, 1, wx.EXPAND | wx.ALL, 5)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(self, wx.ID_OK, "Add")
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 5)
        
        self.SetSizer(sizer)
    
    def GetValue(self):
        """Get the ingredient data"""
        wx_date = self.acc_date.GetValue()
        acc_date_value = date(wx_date.year, wx_date.month + 1, wx_date.day)
        
        return {
            "ingredientID": self.ingredient_id.GetValue().strip() or None,
            "ingredient_type": self.ingredient_type.GetStringSelection(),
            "acc_date": acc_date_value,
            "source": self.source.GetValue().strip() or None,
            "description": self.description.GetValue().strip() or None,
        }


    def GetValue(self):
        """Get the ingredient data"""
        wx_date = self.acc_date.GetValue()
        acc_date_value = date(wx_date.year, wx_date.month + 1, wx_date.day)
        
        return {
            "ingredientID": self.ingredient_id.GetValue().strip() or None,
            "ingredient_type": self.ingredient_type.GetStringSelection(),
            "acc_date": acc_date_value,
            "source": self.source.GetValue().strip() or None,
            "description": self.description.GetValue().strip() or None,
        }


def build_ingredient_choices(session, allowed_types):
    """Build ingredient choice list"""
    stmt = select(Ingredient).where(Ingredient.ingredient_type.in_(allowed_types))
    ingredients = session.exec(stmt).all()
    return [describe_ingredient(ing) for ing in ingredients], [ing.ingredientID for ing in ingredients]


def build_starter_choices(session):
    """Build starter choice list"""
    starters = session.exec(select(Starter).order_by(Starter.StarterBatch)).all()
    return [describe_starter(st) for st in starters], [st.StarterBatch for st in starters]


class AddRecipeDialog(wx.Dialog):
    """Dialog for adding a new recipe"""
    
    def __init__(self, parent, session):
        super().__init__(parent, title="Add Recipe", size=(600, 700))
        self.session = session
        self.init_ui()
    
    def init_ui(self):
        panel = scrolled.ScrolledPanel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Batch ID
        sizer.Add(wx.StaticText(panel, label="BatchID (e.g., '??[R|P|M]'):"), 0, wx.ALL, 5)
        self.batch_id = wx.TextCtrl(panel)
        self.batch_id.Bind(wx.EVT_TEXT, self.on_batch_id_change)
        sizer.Add(self.batch_id, 0, wx.EXPAND | wx.ALL, 5)
        
        # Batch Number (auto-parsed)
        sizer.Add(wx.StaticText(panel, label="Batch Number (auto-parsed):"), 0, wx.ALL, 5)
        self.batch_number = wx.TextCtrl(panel, style=wx.TE_READONLY)
        sizer.Add(self.batch_number, 0, wx.EXPAND | wx.ALL, 5)
        
        # Style
        sizer.Add(wx.StaticText(panel, label="Style:"), 0, wx.ALL, 5)
        styles = [e.value for e in StyleEnum] + ["-- create new style --"]
        self.style = wx.Choice(panel, choices=styles)
        self.style.SetSelection(0)
        self.style.Bind(wx.EVT_CHOICE, self.on_style_change)
        sizer.Add(self.style, 0, wx.EXPAND | wx.ALL, 5)
        
        self.new_style_name = wx.TextCtrl(panel)
        self.new_style_name.Hide()
        sizer.Add(self.new_style_name, 0, wx.EXPAND | wx.ALL, 5)
        
        # Start Date
        sizer.Add(wx.StaticText(panel, label="Start Date:"), 0, wx.ALL, 5)
        self.start_date = wx.adv.DatePickerCtrl(panel, style=wx.adv.DP_DROPDOWN)
        self.start_date.SetValue(wx.DateTime.Today())
        sizer.Add(self.start_date, 0, wx.EXPAND | wx.ALL, 5)
        
        # Ingredients
        rice_types = [IngredientTypeEnum.RICE.value, IngredientTypeEnum.KAKI_RICE.value]
        koji_types = [IngredientTypeEnum.RICE.value, IngredientTypeEnum.KOJI_RICE.value]
        yeast_types = [IngredientTypeEnum.YEAST.value]
        water_types = [IngredientTypeEnum.WATER.value]
        
        kake_labels, kake_ids = build_ingredient_choices(self.session, rice_types)
        koji_labels, koji_ids = build_ingredient_choices(self.session, koji_types)
        yeast_labels, yeast_ids = build_ingredient_choices(self.session, yeast_types)
        water_labels, water_ids = build_ingredient_choices(self.session, water_types)
        
        sizer.Add(wx.StaticText(panel, label="Kake Rice:"), 0, wx.ALL, 5)
        self.kake = wx.ComboBox(panel, choices=kake_labels, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        if kake_labels:
            self.kake.SetSelection(0)
        self.kake_ids = kake_ids
        sizer.Add(self.kake, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(wx.StaticText(panel, label="Koji Rice:"), 0, wx.ALL, 5)
        self.koji = wx.ComboBox(panel, choices=koji_labels, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        # Default to koji50 if available
        for i, label in enumerate(koji_labels):
            if "koji50" in label.lower():
                self.koji.SetSelection(i)
                break
        if self.koji.GetSelection() == wx.NOT_FOUND and koji_labels:
            self.koji.SetSelection(0)
        self.koji_ids = koji_ids
        sizer.Add(self.koji, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(wx.StaticText(panel, label="Yeast:"), 0, wx.ALL, 5)
        self.yeast = wx.ComboBox(panel, choices=yeast_labels, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        # Default to Prop_sake9 if available
        for i, label in enumerate(yeast_labels):
            if "prop_sake9" in label.lower():
                self.yeast.SetSelection(i)
                break
        if self.yeast.GetSelection() == wx.NOT_FOUND and yeast_labels:
            self.yeast.SetSelection(0)
        self.yeast_ids = yeast_ids
        sizer.Add(self.yeast, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(wx.StaticText(panel, label="Water Type:"), 0, wx.ALL, 5)
        self.water_type = wx.ComboBox(panel, choices=water_labels, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        if water_labels:
            self.water_type.SetSelection(0)
        self.water_ids = water_ids
        sizer.Add(self.water_type, 0, wx.EXPAND | wx.ALL, 5)
        
        # Starter
        starter_labels, starter_ids = build_starter_choices(self.session)
        sizer.Add(wx.StaticText(panel, label="Starter Batch:"), 0, wx.ALL, 5)
        self.starter_batch = wx.ComboBox(panel, choices=["Auto-create default Shubo starter"] + starter_labels,
                                         style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.starter_batch.SetSelection(0)
        self.starter_ids = [None] + starter_ids
        sizer.Add(self.starter_batch, 0, wx.EXPAND | wx.ALL, 5)
        
        # Ferment Temp (default 6C)
        sizer.Add(wx.StaticText(panel, label="Ferment Temp (°C):"), 0, wx.ALL, 5)
        self.ferment_temp = wx.TextCtrl(panel, value="6")
        sizer.Add(self.ferment_temp, 0, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        panel.SetupScrolling()
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(self, wx.ID_OK, "Add")
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 5)
        self.SetSizer(main_sizer)
    
    def on_batch_id_change(self, event):
        """Parse batch number from batchID"""
        batch_id = self.batch_id.GetValue()
        if batch_id:
            numbers = re.findall(r'\d+', batch_id)
            if numbers:
                self.batch_number.SetValue(numbers[-1])
    
    def on_style_change(self, event):
        """Show/hide new style name field"""
        if self.style.GetStringSelection() == "-- create new style --":
            self.new_style_name.Show()
        else:
            self.new_style_name.Hide()
        self.Layout()
    
    def GetValue(self):
        """Get the recipe data"""
        wx_date = self.start_date.GetValue()
        start_date_value = date(wx_date.year, wx_date.month + 1, wx_date.day)
        
        kake_idx = self.kake.GetSelection()
        koji_idx = self.koji.GetSelection()
        yeast_idx = self.yeast.GetSelection()
        water_idx = self.water_type.GetSelection()
        starter_idx = self.starter_batch.GetSelection()
        
        style_value = self.style.GetStringSelection()
        if style_value == "-- create new style --":
            style_value = self.new_style_name.GetValue().strip()
        
        return {
            "batchID": self.batch_id.GetValue().strip(),
            "batch": int(self.batch_number.GetValue()) if self.batch_number.GetValue() else None,
            "style": style_value,
            "start_date": start_date_value,
            "kake": self.kake_ids[kake_idx] if kake_idx >= 0 else None,
            "koji": self.koji_ids[koji_idx] if koji_idx >= 0 else None,
            "yeast": self.yeast_ids[yeast_idx] if yeast_idx >= 0 else None,
            "water_type": self.water_ids[water_idx] if water_idx >= 0 else None,
            "starter": self.starter_ids[starter_idx] if starter_idx >= 0 else None,
            "ferment_temp_C": float(self.ferment_temp.GetValue()) if self.ferment_temp.GetValue() else 6.0,
        }


class AddStarterDialog(wx.Dialog):
    """Dialog for adding a new starter"""
    
    def __init__(self, parent, session):
        super().__init__(parent, title="Add Starter", size=(500, 600))
        self.session = session
        self.init_ui()
    
    def init_ui(self):
        panel = scrolled.ScrolledPanel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Starter Batch
        sizer.Add(wx.StaticText(panel, label="StarterBatch (e.g., s64):"), 0, wx.ALL, 5)
        self.starter_batch = wx.TextCtrl(panel)
        sizer.Add(self.starter_batch, 0, wx.EXPAND | wx.ALL, 5)
        
        # Date
        sizer.Add(wx.StaticText(panel, label="Date:"), 0, wx.ALL, 5)
        self.starter_date = wx.adv.DatePickerCtrl(panel, style=wx.adv.DP_DROPDOWN)
        self.starter_date.SetValue(wx.DateTime.Today())
        sizer.Add(self.starter_date, 0, wx.EXPAND | wx.ALL, 5)
        
        # Batch ID
        sizer.Add(wx.StaticText(panel, label="BatchID (optional):"), 0, wx.ALL, 5)
        self.batch_id = wx.TextCtrl(panel)
        sizer.Add(self.batch_id, 0, wx.EXPAND | wx.ALL, 5)
        
        # Ingredients
        rice_types = [IngredientTypeEnum.RICE.value, IngredientTypeEnum.KAKI_RICE.value]
        koji_types = [IngredientTypeEnum.RICE.value, IngredientTypeEnum.KOJI_RICE.value]
        yeast_types = [IngredientTypeEnum.YEAST.value]
        water_types = [IngredientTypeEnum.WATER.value]
        
        kake_labels, kake_ids = build_ingredient_choices(self.session, rice_types)
        koji_labels, koji_ids = build_ingredient_choices(self.session, koji_types)
        yeast_labels, yeast_ids = build_ingredient_choices(self.session, yeast_types)
        water_labels, water_ids = build_ingredient_choices(self.session, water_types)
        
        sizer.Add(wx.StaticText(panel, label="Kake:"), 0, wx.ALL, 5)
        self.kake = wx.ComboBox(panel, choices=kake_labels, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        if kake_labels:
            self.kake.SetSelection(0)
        self.kake_ids = kake_ids
        sizer.Add(self.kake, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(wx.StaticText(panel, label="Koji:"), 0, wx.ALL, 5)
        self.koji = wx.ComboBox(panel, choices=koji_labels, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        if koji_labels:
            self.koji.SetSelection(0)
        self.koji_ids = koji_ids
        sizer.Add(self.koji, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(wx.StaticText(panel, label="Yeast:"), 0, wx.ALL, 5)
        self.yeast = wx.ComboBox(panel, choices=yeast_labels, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        if yeast_labels:
            self.yeast.SetSelection(0)
        self.yeast_ids = yeast_ids
        sizer.Add(self.yeast, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(wx.StaticText(panel, label="Water Type:"), 0, wx.ALL, 5)
        self.water_type = wx.ComboBox(panel, choices=water_labels, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        if water_labels:
            self.water_type.SetSelection(0)
        self.water_ids = water_ids
        sizer.Add(self.water_type, 0, wx.EXPAND | wx.ALL, 5)
        
        # Amounts
        sizer.Add(wx.StaticText(panel, label="Amt_Kake (g):"), 0, wx.ALL, 5)
        self.amt_kake = wx.TextCtrl(panel)
        sizer.Add(self.amt_kake, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(wx.StaticText(panel, label="Amt_Koji (g):"), 0, wx.ALL, 5)
        self.amt_koji = wx.TextCtrl(panel)
        sizer.Add(self.amt_koji, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(wx.StaticText(panel, label="Amt_water (mL):"), 0, wx.ALL, 5)
        self.amt_water = wx.TextCtrl(panel)
        sizer.Add(self.amt_water, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(wx.StaticText(panel, label="Lactic Acid (g):"), 0, wx.ALL, 5)
        self.lactic_acid = wx.TextCtrl(panel)
        sizer.Add(self.lactic_acid, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(wx.StaticText(panel, label="MgSO4 (g):"), 0, wx.ALL, 5)
        self.mgso4 = wx.TextCtrl(panel)
        sizer.Add(self.mgso4, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(wx.StaticText(panel, label="KCl (g):"), 0, wx.ALL, 5)
        self.kcl = wx.TextCtrl(panel)
        sizer.Add(self.kcl, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(wx.StaticText(panel, label="Temp (°C):"), 0, wx.ALL, 5)
        self.temp = wx.TextCtrl(panel)
        sizer.Add(self.temp, 0, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        panel.SetupScrolling()
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(self, wx.ID_OK, "Add")
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 5)
        self.SetSizer(main_sizer)
    
    def GetValue(self):
        """Get the starter data"""
        wx_date = self.starter_date.GetValue()
        date_value = date(wx_date.year, wx_date.month + 1, wx_date.day)
        
        starter_batch_str = self.starter_batch.GetValue().strip()
        if starter_batch_str and not starter_batch_str.lower().startswith('s'):
            try:
                batch_num = int(starter_batch_str)
                starter_batch_str = f"s{batch_num}"
            except ValueError:
                starter_batch_str = f"s{starter_batch_str}"
        
        kake_idx = self.kake.GetSelection()
        koji_idx = self.koji.GetSelection()
        yeast_idx = self.yeast.GetSelection()
        water_idx = self.water_type.GetSelection()
        
        return {
            "StarterBatch": starter_batch_str or None,
            "Date": date_value,
            "BatchID": self.batch_id.GetValue().strip() or None,
            "Kake": self.kake_ids[kake_idx] if kake_idx >= 0 else None,
            "Koji": self.koji_ids[koji_idx] if koji_idx >= 0 else None,
            "yeast": self.yeast_ids[yeast_idx] if yeast_idx >= 0 else None,
            "water_type": self.water_ids[water_idx] if water_idx >= 0 else None,
            "Amt_Kake": float(self.amt_kake.GetValue()) if self.amt_kake.GetValue() else None,
            "Amt_Koji": float(self.amt_koji.GetValue()) if self.amt_koji.GetValue() else None,
            "Amt_water": float(self.amt_water.GetValue()) if self.amt_water.GetValue() else None,
            "lactic_acid": float(self.lactic_acid.GetValue()) if self.lactic_acid.GetValue() else None,
            "MgSO4": float(self.mgso4.GetValue()) if self.mgso4.GetValue() else None,
            "KCl": float(self.kcl.GetValue()) if self.kcl.GetValue() else None,
            "temp_C": float(self.temp.GetValue()) if self.temp.GetValue() else None,
        }


class AddPublishNoteDialog(wx.Dialog):
    """Dialog for adding a publish note"""
    
    def __init__(self, parent, session):
        super().__init__(parent, title="Add Publish Note", size=(500, 400))
        self.session = session
        self.init_ui()
    
    def init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Batch ID
        sizer.Add(wx.StaticText(self, label="BatchID:"), 0, wx.ALL, 5)
        recipes = self.session.exec(select(Recipe.batchID).where(Recipe.batchID.isnot(None))).all()
        batch_ids = [str(bid) for bid in recipes if bid]
        self.batch_id = wx.ComboBox(self, choices=batch_ids, style=wx.CB_DROPDOWN)
        sizer.Add(self.batch_id, 0, wx.EXPAND | wx.ALL, 5)
        
        # Pouch Date
        sizer.Add(wx.StaticText(self, label="Pouch Date:"), 0, wx.ALL, 5)
        self.pouch_date = wx.adv.DatePickerCtrl(self, style=wx.adv.DP_DROPDOWN)
        self.pouch_date.SetValue(wx.DateTime.Today())
        sizer.Add(self.pouch_date, 0, wx.EXPAND | wx.ALL, 5)
        
        # Style
        sizer.Add(wx.StaticText(self, label="Style:"), 0, wx.ALL, 5)
        styles = [e.value for e in StyleEnum]
        self.style = wx.Choice(self, choices=styles)
        sizer.Add(self.style, 0, wx.EXPAND | wx.ALL, 5)
        
        # Water
        water_types = [IngredientTypeEnum.WATER.value]
        water_labels, water_ids = build_ingredient_choices(self.session, water_types)
        sizer.Add(wx.StaticText(self, label="Water:"), 0, wx.ALL, 5)
        self.water = wx.ComboBox(self, choices=water_labels, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        if water_labels:
            self.water.SetSelection(0)
        self.water_ids = water_ids
        sizer.Add(self.water, 0, wx.EXPAND | wx.ALL, 5)
        
        # Description
        sizer.Add(wx.StaticText(self, label="Description:"), 0, wx.ALL, 5)
        self.description = wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(-1, 150))
        sizer.Add(self.description, 1, wx.EXPAND | wx.ALL, 5)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(self, wx.ID_OK, "Add")
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 5)
        
        self.SetSizer(sizer)
    
    def GetValue(self):
        """Get the publish note data"""
        wx_date = self.pouch_date.GetValue()
        pouch_date_value = date(wx_date.year, wx_date.month + 1, wx_date.day)
        
        water_idx = self.water.GetSelection()
        
        return {
            "BatchID": self.batch_id.GetValue().strip(),
            "Pouch_Date": pouch_date_value,
            "Style": self.style.GetStringSelection(),
            "Water": self.water_ids[water_idx] if water_idx >= 0 else None,
            "Description": self.description.GetValue().strip(),
        }


class UpdateRecipeDialog(wx.Dialog):
    """Dialog for updating a recipe"""
    
    def __init__(self, parent, session, recipe):
        super().__init__(parent, title="Update Recipe", size=(600, 700))
        self.session = session
        self.recipe = recipe
        self.init_ui()
        self.load_recipe_data()
    
    def init_ui(self):
        panel = scrolled.ScrolledPanel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Update type
        sizer.Add(wx.StaticText(panel, label="Update Type:"), 0, wx.ALL, 5)
        update_types = ["addition1", "addition2", "addition3", "ferment_finish", "batch_finishing"]
        self.update_type = wx.Choice(panel, choices=update_types)
        self.update_type.Bind(wx.EVT_CHOICE, self.on_update_type_change)
        sizer.Add(self.update_type, 0, wx.EXPAND | wx.ALL, 5)
        
        # Fields container
        self.fields_panel = wx.Panel(panel)
        self.fields_sizer = wx.BoxSizer(wx.VERTICAL)
        self.fields_panel.SetSizer(self.fields_sizer)
        sizer.Add(self.fields_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        panel.SetupScrolling()
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(self, wx.ID_OK, "Update")
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 5)
        self.SetSizer(main_sizer)
        
        self.field_controls = {}
        self.on_update_type_change(None)
    
    def load_recipe_data(self):
        """Load existing recipe data"""
        pass  # Could pre-populate fields
    
    def on_update_type_change(self, event):
        """Show/hide fields based on update type"""
        # Clear existing fields
        for child in self.fields_panel.GetChildren():
            child.Destroy()
        self.fields_sizer.Clear()
        self.field_controls = {}
        
        update_type = self.update_type.GetStringSelection()
        
        if update_type in ["addition1", "addition2", "addition3"]:
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label=f"{update_type.capitalize()} Kake Rice (g):"), 0, wx.ALL, 5)
            kake_field = wx.TextCtrl(self.fields_panel)
            self.fields_sizer.Add(kake_field, 0, wx.EXPAND | wx.ALL, 5)
            self.field_controls["kake_g"] = kake_field
            
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label=f"{update_type.capitalize()} Koji Rice (g):"), 0, wx.ALL, 5)
            koji_field = wx.TextCtrl(self.fields_panel)
            self.fields_sizer.Add(koji_field, 0, wx.EXPAND | wx.ALL, 5)
            self.field_controls["koji_g"] = koji_field
            
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label=f"{update_type.capitalize()} Notes:"), 0, wx.ALL, 5)
            notes_field = wx.TextCtrl(self.fields_panel, style=wx.TE_MULTILINE, size=(-1, 80))
            self.fields_sizer.Add(notes_field, 1, wx.EXPAND | wx.ALL, 5)
            self.field_controls["notes"] = notes_field
            
        elif update_type == "ferment_finish":
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label="Ferment Finish Gravity:"), 0, wx.ALL, 5)
            gravity_field = wx.TextCtrl(self.fields_panel)
            self.fields_sizer.Add(gravity_field, 0, wx.EXPAND | wx.ALL, 5)
            self.field_controls["ferment_finish_gravity"] = gravity_field
            
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label="Ferment Finish Brix (%):"), 0, wx.ALL, 5)
            brix_field = wx.TextCtrl(self.fields_panel)
            self.fields_sizer.Add(brix_field, 0, wx.EXPAND | wx.ALL, 5)
            self.field_controls["ferment_finish_brix"] = brix_field
            
        elif update_type == "batch_finishing":
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label="Final Measured Temp (°C):"), 0, wx.ALL, 5)
            temp_field = wx.TextCtrl(self.fields_panel)
            self.fields_sizer.Add(temp_field, 0, wx.EXPAND | wx.ALL, 5)
            self.field_controls["final_measured_temp_C"] = temp_field
            
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label="Calibrated Temp (°C):"), 0, wx.ALL, 5)
            calib_choice = wx.Choice(self.fields_panel, choices=["20", "15.6"])
            calib_choice.SetSelection(0)
            self.fields_sizer.Add(calib_choice, 0, wx.EXPAND | wx.ALL, 5)
            self.field_controls["calibrated_temp"] = calib_choice
            
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label="Final Measured Brix (%):"), 0, wx.ALL, 5)
            brix_field = wx.TextCtrl(self.fields_panel)
            self.fields_sizer.Add(brix_field, 0, wx.EXPAND | wx.ALL, 5)
            self.field_controls["final_measured_Brix_pct"] = brix_field
            
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label="Final Measured Gravity:"), 0, wx.ALL, 5)
            gravity_field = wx.TextCtrl(self.fields_panel)
            self.fields_sizer.Add(gravity_field, 0, wx.EXPAND | wx.ALL, 5)
            self.field_controls["final_measured_gravity"] = gravity_field
            
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label="Final Water Addition (mL):"), 0, wx.ALL, 5)
            water_field = wx.TextCtrl(self.fields_panel)
            self.fields_sizer.Add(water_field, 0, wx.EXPAND | wx.ALL, 5)
            self.field_controls["final_water_addition_mL"] = water_field
            
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label="Clarified:"), 0, wx.ALL, 5)
            clarified_check = wx.CheckBox(self.fields_panel)
            self.fields_sizer.Add(clarified_check, 0, wx.ALL, 5)
            self.field_controls["clarified"] = clarified_check
            
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label="Pasteurized:"), 0, wx.ALL, 5)
            pasteurized_check = wx.CheckBox(self.fields_panel)
            self.fields_sizer.Add(pasteurized_check, 0, wx.ALL, 5)
            self.field_controls["pasteurized"] = pasteurized_check
            
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label="Pasteurization Notes:"), 0, wx.ALL, 5)
            pasteur_notes = wx.TextCtrl(self.fields_panel, style=wx.TE_MULTILINE, size=(-1, 60))
            self.fields_sizer.Add(pasteur_notes, 0, wx.EXPAND | wx.ALL, 5)
            self.field_controls["pasteurization_notes"] = pasteur_notes
            
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label="Finishing Additions:"), 0, wx.ALL, 5)
            finishing = wx.TextCtrl(self.fields_panel, style=wx.TE_MULTILINE, size=(-1, 60))
            self.fields_sizer.Add(finishing, 0, wx.EXPAND | wx.ALL, 5)
            self.field_controls["finishing_additions"] = finishing
            
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label="Publish Comment:"), 0, wx.ALL, 5)
            publish_comment = wx.TextCtrl(self.fields_panel, style=wx.TE_MULTILINE, size=(-1, 80))
            self.fields_sizer.Add(publish_comment, 1, wx.EXPAND | wx.ALL, 5)
            self.field_controls["publish_comment"] = publish_comment
            
            self.fields_sizer.Add(wx.StaticText(self.fields_panel, label="Pouch Date:"), 0, wx.ALL, 5)
            pouch_date = wx.adv.DatePickerCtrl(self.fields_panel, style=wx.adv.DP_DROPDOWN)
            self.fields_sizer.Add(pouch_date, 0, wx.EXPAND | wx.ALL, 5)
            self.field_controls["pouch_date"] = pouch_date
        
        self.fields_panel.Layout()
        self.Layout()
    
    def GetValue(self):
        """Get the update data"""
        update_type = self.update_type.GetStringSelection()
        data = {"update_type": update_type}
        
        for key, control in self.field_controls.items():
            if isinstance(control, wx.TextCtrl):
                value = control.GetValue().strip()
                if value:
                    try:
                        data[key] = float(value)
                    except ValueError:
                        data[key] = value
            elif isinstance(control, wx.CheckBox):
                data[key] = control.GetValue()
            elif isinstance(control, wx.Choice):
                data[key] = float(control.GetStringSelection()) if control.GetStringSelection() else None
            elif isinstance(control, wx.adv.DatePickerCtrl):
                wx_date = control.GetValue()
                data[key] = date(wx_date.year, wx_date.month + 1, wx_date.day)
        
        return data


class GoogleSyncPanel(wx.Panel):
    """Panel for launching Google Sheets sync actions"""
    
    def __init__(self, parent, frame):
        super().__init__(parent)
        self.frame = frame
        self.init_ui()
    
    def init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        info = wx.StaticText(
            self,
            label="Sync the local database with the SakeMonkey Google Sheet.\n"
                  "Enter a custom Spreadsheet ID if needed, otherwise the default is used."
        )
        info.Wrap(500)
        main_sizer.Add(info, 0, wx.ALL, 10)
        
        id_sizer = wx.BoxSizer(wx.HORIZONTAL)
        id_sizer.Add(wx.StaticText(self, label="Spreadsheet ID:"), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.spreadsheet_id = wx.TextCtrl(self, value=DEFAULT_SPREADSHEET_ID)
        id_sizer.Add(self.spreadsheet_id, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(id_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sync_from_btn = wx.Button(self, label="Sync From Google Sheets")
        sync_from_btn.Bind(wx.EVT_BUTTON, self.on_sync_from)
        button_sizer.Add(sync_from_btn, 0, wx.ALL, 5)
        
        sync_to_btn = wx.Button(self, label="Sync To Google Sheets")
        sync_to_btn.Bind(wx.EVT_BUTTON, self.on_sync_to)
        button_sizer.Add(sync_to_btn, 0, wx.ALL, 5)
        main_sizer.Add(button_sizer, 0, wx.ALL, 5)
        
        self.SetSizer(main_sizer)
    
    def get_spreadsheet_id(self) -> str:
        """Return the spreadsheet ID, defaulting if the field is blank"""
        value = self.spreadsheet_id.GetValue().strip()
        return value or DEFAULT_SPREADSHEET_ID
    
    def _refresh_data_tabs(self):
        """Refresh data grids after a sync"""
        if hasattr(self.frame, "refresh_data_tabs"):
            self.frame.refresh_data_tabs()
    
    def on_sync_from(self, event):
        """Handle sync-from button"""
        spreadsheet_id = self.get_spreadsheet_id()
        try:
            sync_from_google_sheets(spreadsheet_id)
            wx.MessageBox("Sync completed successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
            self._refresh_data_tabs()
        except Exception as e:
            wx.MessageBox(f"Error syncing: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_sync_to(self, event):
        """Handle sync-to button"""
        spreadsheet_id = self.get_spreadsheet_id()
        try:
            sync_to_google_sheets(spreadsheet_id)
            wx.MessageBox("Backup completed successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Error backing up: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)


class MainFrame(wx.Frame):
    """Main application window"""
    
    def __init__(self):
        super().__init__(None, title="SakeMonkey Recipe Database", size=(1400, 900))
        self.session = get_session()
        self.init_ui()
        self.Center()
    
    def init_ui(self):
        # Menu bar
        menubar = wx.MenuBar()
        
        file_menu = wx.Menu()
        sync_from_item = file_menu.Append(wx.ID_ANY, "Sync from Google Sheets", "Sync data from master Google Sheet")
        self.Bind(wx.EVT_MENU, self.on_sync_from_google_sheets, sync_from_item)
        sync_to_item = file_menu.Append(wx.ID_ANY, "Sync to Google Sheets", "Backup data to Google Sheet")
        self.Bind(wx.EVT_MENU, self.on_sync_to_google_sheets, sync_to_item)
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "Exit", "Exit application")
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        
        menubar.Append(file_menu, "File")
        self.SetMenuBar(menubar)
        
        # Notebook for tabs
        notebook = wx.Notebook(self)
        
        # Ingredients tab
        ingredients_panel = DataGridPanel(notebook, Ingredient, self.session)
        notebook.AddPage(ingredients_panel, "Ingredients")
        
        # Recipes tab
        recipes_panel = DataGridPanel(notebook, Recipe, self.session)
        notebook.AddPage(recipes_panel, "Recipes")
        
        # Starters tab
        starters_panel = DataGridPanel(notebook, Starter, self.session)
        notebook.AddPage(starters_panel, "Starters")
        
        # Publish Notes tab
        publish_panel = DataGridPanel(notebook, PublishNote, self.session)
        notebook.AddPage(publish_panel, "Publish Notes")
        
        # Formulas tab
        formulas_panel = FormulasPanel(notebook, self.session)
        notebook.AddPage(formulas_panel, "Formulas")
        
        # Google Sync tab
        google_sync_panel = GoogleSyncPanel(notebook, self)
        notebook.AddPage(google_sync_panel, "Google Sync")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)
    
        self.notebook = notebook
    
    def refresh_data_tabs(self):
        """Refresh all notebook pages that expose a load_data method"""
        if not hasattr(self, "notebook"):
            return
        for i in range(self.notebook.GetPageCount()):
            page = self.notebook.GetPage(i)
            if hasattr(page, "load_data"):
                page.load_data()
    
    def on_sync_from_google_sheets(self, event):
        """Sync from Google Sheets"""
        dlg = wx.TextEntryDialog(
            self,
            "Enter Google Sheets Spreadsheet ID:",
            "Sync from Google Sheets",
            DEFAULT_SPREADSHEET_ID
        )
        if dlg.ShowModal() == wx.ID_OK:
            spreadsheet_id = dlg.GetValue().strip()
            if not spreadsheet_id:
                spreadsheet_id = DEFAULT_SPREADSHEET_ID
            try:
                sync_from_google_sheets(spreadsheet_id)
                wx.MessageBox("Sync completed successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
                self.refresh_data_tabs()
            except Exception as e:
                wx.MessageBox(f"Error syncing: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()
    
    def on_sync_to_google_sheets(self, event):
        """Sync to Google Sheets"""
        dlg = wx.TextEntryDialog(
            self,
            "Enter Google Sheets Spreadsheet ID:",
            "Sync to Google Sheets",
            DEFAULT_SPREADSHEET_ID
        )
        if dlg.ShowModal() == wx.ID_OK:
            spreadsheet_id = dlg.GetValue().strip()
            if not spreadsheet_id:
                spreadsheet_id = DEFAULT_SPREADSHEET_ID
            try:
                sync_to_google_sheets(spreadsheet_id)
                wx.MessageBox("Backup completed successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"Error backing up: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()
    
    def on_exit(self, event):
        self.Close()
    
    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()


class SakeMonkeyApp(wx.App):
    """Main application"""
    
    def OnInit(self):
        # Initialize database
        init_database()
        frame = MainFrame()
        frame.Show()
        return True


def main():
    app = SakeMonkeyApp()
    app.MainLoop()


if __name__ == "__main__":
    main()
