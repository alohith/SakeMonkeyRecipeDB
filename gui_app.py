"""
SakeMonkey Recipe Database GUI Application
Built with wxPython (Gooey backend) for full database interface
"""
import wx
import wx.grid
from datetime import date, datetime
from sqlmodel import Session, select
from database import get_session, init_database
from models import Ingredient, Recipe, Starter, PublishNote
from formulas import calculate_final_gravity, calculate_abv, calculate_smv, calculate_dilution_adjustment
from google_sheets_sync import sync_from_google_sheets
import os


class FormulasPanel(wx.Panel):
    """Panel for formula calculations"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(self, label="Sake Brewing Formulas Calculator")
        title_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL | wx.CENTER, 10)
        
        # Gravity Correction Calculator
        gravity_box = wx.StaticBox(self, label="Gravity Correction Calculator")
        gravity_sizer = wx.StaticBoxSizer(gravity_box, wx.VERTICAL)
        
        grid = wx.FlexGridSizer(4, 2, 5, 5)
        
        grid.Add(wx.StaticText(self, label="Calibrated Temp (°C):"), 0, wx.ALL, 5)
        self.calibrated_temp = wx.TextCtrl(self, value="20.0")
        grid.Add(self.calibrated_temp, 0, wx.EXPAND | wx.ALL, 5)
        
        grid.Add(wx.StaticText(self, label="Measured Temp (°C):"), 0, wx.ALL, 5)
        self.measured_temp = wx.TextCtrl(self)
        grid.Add(self.measured_temp, 0, wx.EXPAND | wx.ALL, 5)
        
        grid.Add(wx.StaticText(self, label="Measured Gravity:"), 0, wx.ALL, 5)
        self.measured_gravity = wx.TextCtrl(self)
        grid.Add(self.measured_gravity, 0, wx.EXPAND | wx.ALL, 5)
        
        grid.Add(wx.StaticText(self, label="Corrected Gravity:"), 0, wx.ALL, 5)
        self.corrected_gravity = wx.TextCtrl(self, style=wx.TE_READONLY)
        grid.Add(self.corrected_gravity, 0, wx.EXPAND | wx.ALL, 5)
        
        gravity_sizer.Add(grid, 0, wx.ALL, 10)
        
        calc_btn = wx.Button(self, label="Calculate Corrected Gravity")
        calc_btn.Bind(wx.EVT_BUTTON, self.on_calculate_gravity)
        gravity_sizer.Add(calc_btn, 0, wx.ALL | wx.CENTER, 5)
        
        main_sizer.Add(gravity_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # ABV and SMV Calculator
        abv_box = wx.StaticBox(self, label="ABV% and SMV Calculator")
        abv_sizer = wx.StaticBoxSizer(abv_box, wx.VERTICAL)
        
        abv_grid = wx.FlexGridSizer(4, 2, 5, 5)
        
        abv_grid.Add(wx.StaticText(self, label="Brix (%):"), 0, wx.ALL, 5)
        self.brix_input = wx.TextCtrl(self)
        abv_grid.Add(self.brix_input, 0, wx.EXPAND | wx.ALL, 5)
        
        abv_grid.Add(wx.StaticText(self, label="Final Gravity:"), 0, wx.ALL, 5)
        self.final_gravity_input = wx.TextCtrl(self)
        abv_grid.Add(self.final_gravity_input, 0, wx.EXPAND | wx.ALL, 5)
        
        abv_grid.Add(wx.StaticText(self, label="ABV%:"), 0, wx.ALL, 5)
        self.abv_result = wx.TextCtrl(self, style=wx.TE_READONLY)
        abv_grid.Add(self.abv_result, 0, wx.EXPAND | wx.ALL, 5)
        
        abv_grid.Add(wx.StaticText(self, label="SMV:"), 0, wx.ALL, 5)
        self.smv_result = wx.TextCtrl(self, style=wx.TE_READONLY)
        abv_grid.Add(self.smv_result, 0, wx.EXPAND | wx.ALL, 5)
        
        abv_sizer.Add(abv_grid, 0, wx.ALL, 10)
        
        calc_abv_btn = wx.Button(self, label="Calculate ABV% and SMV")
        calc_abv_btn.Bind(wx.EVT_BUTTON, self.on_calculate_abv_smv)
        abv_sizer.Add(calc_abv_btn, 0, wx.ALL | wx.CENTER, 5)
        
        main_sizer.Add(abv_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Dilution Calculator
        dilution_box = wx.StaticBox(self, label="Dilution Calculator")
        dilution_sizer = wx.StaticBoxSizer(dilution_box, wx.VERTICAL)
        
        dilution_grid = wx.FlexGridSizer(6, 2, 5, 5)
        
        dilution_grid.Add(wx.StaticText(self, label="Current Brix (%):"), 0, wx.ALL, 5)
        self.curr_brix = wx.TextCtrl(self)
        dilution_grid.Add(self.curr_brix, 0, wx.EXPAND | wx.ALL, 5)
        
        dilution_grid.Add(wx.StaticText(self, label="Current Gravity:"), 0, wx.ALL, 5)
        self.curr_gravity = wx.TextCtrl(self)
        dilution_grid.Add(self.curr_gravity, 0, wx.EXPAND | wx.ALL, 5)
        
        dilution_grid.Add(wx.StaticText(self, label="Current Volume (L):"), 0, wx.ALL, 5)
        self.curr_volume = wx.TextCtrl(self)
        dilution_grid.Add(self.curr_volume, 0, wx.EXPAND | wx.ALL, 5)
        
        target_style = wx.Choice(self, choices=["Pure (11% brix, 1.005 SG)", "Mixer (12% brix, 0.995 SG)"])
        dilution_grid.Add(wx.StaticText(self, label="Target Profile:"), 0, wx.ALL, 5)
        dilution_grid.Add(target_style, 0, wx.EXPAND | wx.ALL, 5)
        self.target_style = target_style
        
        dilution_grid.Add(wx.StaticText(self, label="Water to Add (L):"), 0, wx.ALL, 5)
        self.water_to_add = wx.TextCtrl(self, style=wx.TE_READONLY)
        dilution_grid.Add(self.water_to_add, 0, wx.EXPAND | wx.ALL, 5)
        
        dilution_sizer.Add(dilution_grid, 0, wx.ALL, 10)
        
        calc_dilution_btn = wx.Button(self, label="Calculate Dilution")
        calc_dilution_btn.Bind(wx.EVT_BUTTON, self.on_calculate_dilution)
        dilution_sizer.Add(calc_dilution_btn, 0, wx.ALL | wx.CENTER, 5)
        
        main_sizer.Add(dilution_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
    
    def on_calculate_gravity(self, event):
        try:
            mt = float(self.measured_temp.GetValue())
            mg = float(self.measured_gravity.GetValue())
            ct = float(self.calibrated_temp.GetValue())
            result = calculate_final_gravity(mt, mg, ct)
            self.corrected_gravity.SetValue(str(result))
        except ValueError:
            wx.MessageBox("Please enter valid numeric values", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_calculate_abv_smv(self, event):
        try:
            brix = float(self.brix_input.GetValue())
            fg = float(self.final_gravity_input.GetValue())
            abv = calculate_abv(brix, fg)
            smv = calculate_smv(fg)
            self.abv_result.SetValue(str(abv) if abv else "")
            self.smv_result.SetValue(str(smv) if smv else "")
        except ValueError:
            wx.MessageBox("Please enter valid numeric values", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_calculate_dilution(self, event):
        try:
            curr_brix = float(self.curr_brix.GetValue())
            curr_gravity = float(self.curr_gravity.GetValue())
            curr_vol = float(self.curr_volume.GetValue())
            
            target_idx = self.target_style.GetSelection()
            if target_idx == 0:  # Pure
                target_brix = 11.0
                target_gravity = 1.005
            else:  # Mixer
                target_brix = 12.0
                target_gravity = 0.995
            
            result = calculate_dilution_adjustment(
                curr_brix, curr_gravity, target_brix, target_gravity, curr_vol
            )
            self.water_to_add.SetValue(str(result['water_to_add_L']))
        except ValueError:
            wx.MessageBox("Please enter valid numeric values", "Error", wx.OK | wx.ICON_ERROR)


class DataGridPanel(wx.Panel):
    """Generic panel for displaying and editing database tables"""
    
    def __init__(self, parent, model_class, session):
        super().__init__(parent)
        self.model_class = model_class
        self.session = session
        self.init_ui()
        self.load_data()
    
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
        
        delete_btn = wx.Button(self, label="Delete Selected")
        delete_btn.Bind(wx.EVT_BUTTON, self.on_delete)
        toolbar.Add(delete_btn, 0, wx.ALL, 5)
        
        sizer.Add(toolbar, 0, wx.ALL, 5)
        
        # Grid
        self.grid = wx.grid.Grid(self)
        sizer.Add(self.grid, 1, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(sizer)
    
    def load_data(self):
        statement = select(self.model_class)
        results = self.session.exec(statement).all()
        
        if not results:
            self.grid.CreateGrid(0, 0)
            return
        
        # Get column names from first result
        first = results[0]
        columns = [key for key in first.dict().keys()]
        
        self.grid.CreateGrid(len(results), len(columns))
        
        # Set column labels
        for i, col in enumerate(columns):
            self.grid.SetColLabelValue(i, col)
        
        # Populate data
        for row_idx, obj in enumerate(results):
            data = obj.dict()
            for col_idx, col in enumerate(columns):
                value = data.get(col, "")
                if value is None:
                    value = ""
                elif isinstance(value, date):
                    value = value.isoformat()
                else:
                    value = str(value)
                self.grid.SetCellValue(row_idx, col_idx, value)
        
        self.grid.AutoSizeColumns()
        self.session.commit()
    
    def on_add(self, event):
        # Simple add dialog - would need model-specific dialogs
        wx.MessageBox("Add functionality - implement model-specific dialog", "Info", wx.OK)
    
    def on_delete(self, event):
        selected = self.grid.GetSelectedRows()
        if not selected:
            wx.MessageBox("Please select a row to delete", "Info", wx.OK)
            return
        # Implement delete logic
        wx.MessageBox("Delete functionality - implement deletion logic", "Info", wx.OK)


class MainFrame(wx.Frame):
    """Main application window"""
    
    def __init__(self):
        super().__init__(None, title="SakeMonkey Recipe Database", size=(1200, 800))
        self.session = get_session()
        self.init_ui()
        self.Center()
    
    def init_ui(self):
        # Menu bar
        menubar = wx.MenuBar()
        
        file_menu = wx.Menu()
        sync_item = file_menu.Append(wx.ID_ANY, "Sync from Google Sheets", "Sync data from master Google Sheet")
        self.Bind(wx.EVT_MENU, self.on_sync_google_sheets, sync_item)
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
        formulas_panel = FormulasPanel(notebook)
        notebook.AddPage(formulas_panel, "Formulas")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)
    
    def on_sync_google_sheets(self, event):
        dlg = wx.TextEntryDialog(self, "Enter Google Sheets Spreadsheet ID:", "Sync from Google Sheets")
        if dlg.ShowModal() == wx.ID_OK:
            spreadsheet_id = dlg.GetValue()
            try:
                sync_from_google_sheets(spreadsheet_id)
                wx.MessageBox("Sync completed successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
                # Refresh all tabs
                for i in range(self.GetChildren()[0].GetPageCount()):
                    page = self.GetChildren()[0].GetPage(i)
                    if hasattr(page, 'load_data'):
                        page.load_data()
            except Exception as e:
                wx.MessageBox(f"Error syncing: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
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
