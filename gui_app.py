#!/usr/bin/env python3
"""
GUI Application for SakeMonkey Recipe Database Management
Provides forms for adding and managing sake brewing data
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime
import os
import threading

# Import Google Sheets sync
try:
    from google_sheets_sync import GoogleSheetsSync
    from google_sheets_config import get_spreadsheet_id, set_spreadsheet_id
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("Google Sheets integration not available. Install required packages:")
    print("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

class SakeRecipeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SakeMonkey Recipe Database Manager")
        self.root.geometry("1000x700")
        
        # Database connection
        self.db_path = 'sake_recipe_db.sqlite'
        if not os.path.exists(self.db_path):
            messagebox.showerror("Error", "Database not found. Please run setup_database.py first.")
            self.root.quit()
            return
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        self.setup_ui()
        self.load_ingredients()
        self.load_recipes()
        self.load_starter_data()
        self.load_publish_data()
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_ingredients_tab()
        self.create_recipes_tab()
        self.create_starters_tab()
        self.create_publish_notes_tab()
        self.create_formulas_tab()
        self.create_view_data_tab()
        
        # Add Google Sheets tab if available
        if GOOGLE_SHEETS_AVAILABLE:
            self.create_google_sheets_tab()
    
    def create_ingredients_tab(self):
        """Create ingredients management tab"""
        ingredients_frame = ttk.Frame(self.notebook)
        self.notebook.add(ingredients_frame, text="Ingredients")
        
        # Title
        title_label = ttk.Label(ingredients_frame, text="Manage Ingredients", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Form frame
        form_frame = ttk.LabelFrame(ingredients_frame, text="Add New Ingredient", padding=10)
        form_frame.pack(fill='x', padx=10, pady=5)
        
        # Form fields
        ttk.Label(form_frame, text="Ingredient ID:").grid(row=0, column=0, sticky='w', pady=2)
        self.ingredient_id_entry = ttk.Entry(form_frame, width=30)
        self.ingredient_id_entry.grid(row=0, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Type:").grid(row=1, column=0, sticky='w', pady=2)
        self.ingredient_type_combo = ttk.Combobox(form_frame, width=27, values=[
            'yeast', 'rice', 'nutrientMix', 'water', 'other'
        ])
        self.ingredient_type_combo.grid(row=1, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky='w', pady=2)
        self.ingredient_desc_entry = ttk.Entry(form_frame, width=30)
        self.ingredient_desc_entry.grid(row=2, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Source:").grid(row=3, column=0, sticky='w', pady=2)
        self.ingredient_source_entry = ttk.Entry(form_frame, width=30)
        self.ingredient_source_entry.grid(row=3, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Accession Date:").grid(row=4, column=0, sticky='w', pady=2)
        self.ingredient_date_entry = ttk.Entry(form_frame, width=30)
        self.ingredient_date_entry.grid(row=4, column=1, pady=2, padx=(5, 0))
        self.ingredient_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Add Ingredient", command=self.add_ingredient).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_ingredient_form).pack(side='left', padx=5)
        
        # Ingredients list
        list_frame = ttk.LabelFrame(ingredients_frame, text="Current Ingredients", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for ingredients
        columns = ('ID', 'Type', 'Description', 'Source', 'Date')
        self.ingredients_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.ingredients_tree.heading(col, text=col)
            self.ingredients_tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.ingredients_tree.yview)
        self.ingredients_tree.configure(yscrollcommand=scrollbar.set)
        
        self.ingredients_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def create_recipes_tab(self):
        """Create recipes management tab"""
        recipes_frame = ttk.Frame(self.notebook)
        self.notebook.add(recipes_frame, text="Recipes")
        
        # Title
        title_label = ttk.Label(recipes_frame, text="Manage Recipes", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Form frame
        form_frame = ttk.LabelFrame(recipes_frame, text="Add New Recipe", padding=10)
        form_frame.pack(fill='x', padx=10, pady=5)
        
        # Form fields
        ttk.Label(form_frame, text="Batch ID:").grid(row=0, column=0, sticky='w', pady=2)
        self.recipe_batch_id_entry = ttk.Entry(form_frame, width=30)
        self.recipe_batch_id_entry.grid(row=0, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Batch Number:").grid(row=0, column=2, sticky='w', pady=2, padx=(20, 0))
        self.recipe_batch_entry = ttk.Entry(form_frame, width=30)
        self.recipe_batch_entry.grid(row=0, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Style:").grid(row=1, column=0, sticky='w', pady=2)
        self.recipe_style_combo = ttk.Combobox(form_frame, width=27, values=[
            'pure', 'rustic', 'rustic_experimental', 'other'
        ])
        self.recipe_style_combo.grid(row=1, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Water Type:").grid(row=1, column=2, sticky='w', pady=2, padx=(20, 0))
        self.recipe_water_combo = ttk.Combobox(form_frame, width=27, values=[
            'well', 'spring', 'filtered', 'distilled', 'other'
        ])
        self.recipe_water_combo.grid(row=1, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Kake Rice:").grid(row=2, column=0, sticky='w', pady=2)
        self.recipe_kake_combo = ttk.Combobox(form_frame, width=27)
        self.recipe_kake_combo.grid(row=2, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Koji Rice:").grid(row=2, column=2, sticky='w', pady=2, padx=(20, 0))
        self.recipe_koji_combo = ttk.Combobox(form_frame, width=27)
        self.recipe_koji_combo.grid(row=2, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Yeast:").grid(row=3, column=0, sticky='w', pady=2)
        self.recipe_yeast_combo = ttk.Combobox(form_frame, width=27)
        self.recipe_yeast_combo.grid(row=3, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Starter:").grid(row=3, column=2, sticky='w', pady=2, padx=(20, 0))
        self.recipe_starter_entry = ttk.Entry(form_frame, width=30)
        self.recipe_starter_entry.grid(row=3, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Start Date:").grid(row=4, column=0, sticky='w', pady=2)
        self.recipe_start_date_entry = ttk.Entry(form_frame, width=30)
        self.recipe_start_date_entry.grid(row=4, column=1, pady=2, padx=(5, 0))
        self.recipe_start_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ttk.Label(form_frame, text="Pouch Date:").grid(row=4, column=2, sticky='w', pady=2, padx=(20, 0))
        self.recipe_pouch_date_entry = ttk.Entry(form_frame, width=30)
        self.recipe_pouch_date_entry.grid(row=4, column=3, pady=2, padx=(5, 0))
        
        # Additional recipe fields
        ttk.Label(form_frame, text="Total Kake (g):").grid(row=5, column=0, sticky='w', pady=2)
        self.recipe_total_kake_entry = ttk.Entry(form_frame, width=30)
        self.recipe_total_kake_entry.grid(row=5, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Total Koji (g):").grid(row=5, column=2, sticky='w', pady=2, padx=(20, 0))
        self.recipe_total_koji_entry = ttk.Entry(form_frame, width=30)
        self.recipe_total_koji_entry.grid(row=5, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Total Water (mL):").grid(row=6, column=0, sticky='w', pady=2)
        self.recipe_total_water_entry = ttk.Entry(form_frame, width=30)
        self.recipe_total_water_entry.grid(row=6, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Ferment Temp (°C):").grid(row=6, column=2, sticky='w', pady=2, padx=(20, 0))
        self.recipe_ferment_temp_entry = ttk.Entry(form_frame, width=30)
        self.recipe_ferment_temp_entry.grid(row=6, column=3, pady=2, padx=(5, 0))
        
        # Addition notes
        ttk.Label(form_frame, text="Addition 1 Notes:").grid(row=7, column=0, sticky='w', pady=2)
        self.recipe_addition1_entry = ttk.Entry(form_frame, width=30)
        self.recipe_addition1_entry.grid(row=7, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Addition 2 Notes:").grid(row=7, column=2, sticky='w', pady=2, padx=(20, 0))
        self.recipe_addition2_entry = ttk.Entry(form_frame, width=30)
        self.recipe_addition2_entry.grid(row=7, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Addition 3 Notes:").grid(row=8, column=0, sticky='w', pady=2)
        self.recipe_addition3_entry = ttk.Entry(form_frame, width=30)
        self.recipe_addition3_entry.grid(row=8, column=1, pady=2, padx=(5, 0))
        
        # Final measurements (maps to final_measured_* fields)
        ttk.Label(form_frame, text="Final Measured Temp (°C):").grid(row=8, column=2, sticky='w', pady=2, padx=(20, 0))
        self.recipe_final_temp_entry = ttk.Entry(form_frame, width=30)
        self.recipe_final_temp_entry.grid(row=8, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Final Measured Gravity:").grid(row=9, column=0, sticky='w', pady=2)
        self.recipe_final_gravity_entry = ttk.Entry(form_frame, width=30)
        self.recipe_final_gravity_entry.grid(row=9, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Final Measured Brix (%):").grid(row=9, column=2, sticky='w', pady=2, padx=(20, 0))
        self.recipe_final_brix_entry = ttk.Entry(form_frame, width=30)
        self.recipe_final_brix_entry.grid(row=9, column=3, pady=2, padx=(5, 0))
        
        # Process checkboxes
        ttk.Label(form_frame, text="Process:").grid(row=10, column=0, sticky='w', pady=2)
        process_frame = ttk.Frame(form_frame)
        process_frame.grid(row=10, column=1, columnspan=3, sticky='w', pady=2, padx=(5, 0))
        
        self.recipe_clarified_var = tk.BooleanVar()
        self.recipe_pasteurized_var = tk.BooleanVar()
        
        ttk.Checkbutton(process_frame, text="Clarified", variable=self.recipe_clarified_var).pack(side='left', padx=5)
        ttk.Checkbutton(process_frame, text="Pasteurized", variable=self.recipe_pasteurized_var).pack(side='left', padx=5)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=11, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="Add Recipe", command=self.add_recipe).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_recipe_form).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Load Ingredients", command=self.load_ingredients).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Refresh List", command=self.load_recipes).pack(side='left', padx=5)
        
        # Recipes list
        list_frame = ttk.LabelFrame(recipes_frame, text="Current Recipes", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for recipes
        columns = ('Batch ID', 'Batch', 'Style', 'Start Date', 'Pouch Date', 'ABV%', 'SMV', 'Status')
        self.recipes_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.recipes_tree.heading(col, text=col)
            self.recipes_tree.column(col, width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.recipes_tree.yview)
        self.recipes_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recipes_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def create_starters_tab(self):
        """Create starters management tab"""
        starters_frame = ttk.Frame(self.notebook)
        self.notebook.add(starters_frame, text="Starters")
        
        # Title
        title_label = ttk.Label(starters_frame, text="Manage Yeast Starters", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Form frame
        form_frame = ttk.LabelFrame(starters_frame, text="Add New Starter", padding=10)
        form_frame.pack(fill='x', padx=10, pady=5)
        
        # Form fields
        ttk.Label(form_frame, text="Date:").grid(row=0, column=0, sticky='w', pady=2)
        self.starter_date_entry = ttk.Entry(form_frame, width=30)
        self.starter_date_entry.grid(row=0, column=1, pady=2, padx=(5, 0))
        self.starter_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ttk.Label(form_frame, text="Starter Batch:").grid(row=0, column=2, sticky='w', pady=2, padx=(20, 0))
        self.starter_batch_entry = ttk.Entry(form_frame, width=30)
        self.starter_batch_entry.grid(row=0, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Batch ID:").grid(row=1, column=0, sticky='w', pady=2)
        self.starter_batch_id_combo = ttk.Combobox(form_frame, width=27)
        self.starter_batch_id_combo.grid(row=1, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Water Type:").grid(row=1, column=2, sticky='w', pady=2, padx=(20, 0))
        self.starter_water_combo = ttk.Combobox(form_frame, width=27, values=[
            'well', 'spring', 'filtered', 'distilled', 'other'
        ])
        self.starter_water_combo.grid(row=1, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Amount Kake (g):").grid(row=2, column=0, sticky='w', pady=2)
        self.starter_amt_kake_entry = ttk.Entry(form_frame, width=30)
        self.starter_amt_kake_entry.grid(row=2, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Amount Koji (g):").grid(row=2, column=2, sticky='w', pady=2, padx=(20, 0))
        self.starter_amt_koji_entry = ttk.Entry(form_frame, width=30)
        self.starter_amt_koji_entry.grid(row=2, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Amount Water (ml):").grid(row=3, column=0, sticky='w', pady=2)
        self.starter_amt_water_entry = ttk.Entry(form_frame, width=30)
        self.starter_amt_water_entry.grid(row=3, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Kake Rice:").grid(row=3, column=2, sticky='w', pady=2, padx=(20, 0))
        self.starter_kake_combo = ttk.Combobox(form_frame, width=27)
        self.starter_kake_combo.grid(row=3, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Koji Rice:").grid(row=4, column=0, sticky='w', pady=2)
        self.starter_koji_combo = ttk.Combobox(form_frame, width=27)
        self.starter_koji_combo.grid(row=4, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Yeast:").grid(row=4, column=2, sticky='w', pady=2, padx=(20, 0))
        self.starter_yeast_combo = ttk.Combobox(form_frame, width=27)
        self.starter_yeast_combo.grid(row=4, column=3, pady=2, padx=(5, 0))
        
        # Additional fields for starter chemistry
        ttk.Label(form_frame, text="Lactic Acid (g):").grid(row=5, column=0, sticky='w', pady=2)
        self.starter_lactic_acid_entry = ttk.Entry(form_frame, width=30)
        self.starter_lactic_acid_entry.grid(row=5, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="MgSO4 (g):").grid(row=5, column=2, sticky='w', pady=2, padx=(20, 0))
        self.starter_mgso4_entry = ttk.Entry(form_frame, width=30)
        self.starter_mgso4_entry.grid(row=5, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="KCl (g):").grid(row=6, column=0, sticky='w', pady=2)
        self.starter_kcl_entry = ttk.Entry(form_frame, width=30)
        self.starter_kcl_entry.grid(row=6, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Temperature (°C):").grid(row=6, column=2, sticky='w', pady=2, padx=(20, 0))
        self.starter_temp_entry = ttk.Entry(form_frame, width=30)
        self.starter_temp_entry.grid(row=6, column=3, pady=2, padx=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=7, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="Add Starter", command=self.add_starter).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_starter_form).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Load Data", command=self.load_starter_data).pack(side='left', padx=5)
        
        # Starters list
        list_frame = ttk.LabelFrame(starters_frame, text="Current Starters", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for starters
        columns = ('Date', 'Starter Batch', 'Batch ID', 'Amt Kake', 'Amt Koji', 'Amt Water', 'Yeast', 'Temp °C')
        self.starters_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.starters_tree.heading(col, text=col)
            self.starters_tree.column(col, width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.starters_tree.yview)
        self.starters_tree.configure(yscrollcommand=scrollbar.set)
        
        self.starters_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def create_publish_notes_tab(self):
        """Create publish notes management tab"""
        publish_frame = ttk.Frame(self.notebook)
        self.notebook.add(publish_frame, text="Publish Notes")
        
        # Title
        title_label = ttk.Label(publish_frame, text="Manage Publish Notes", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Form frame
        form_frame = ttk.LabelFrame(publish_frame, text="Add Publish Notes", padding=10)
        form_frame.pack(fill='x', padx=10, pady=5)
        
        # Form fields
        ttk.Label(form_frame, text="Batch ID:").grid(row=0, column=0, sticky='w', pady=2)
        self.publish_batch_id_combo = ttk.Combobox(form_frame, width=30)
        self.publish_batch_id_combo.grid(row=0, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Pouch Date:").grid(row=0, column=2, sticky='w', pady=2, padx=(20, 0))
        self.publish_pouch_date_entry = ttk.Entry(form_frame, width=30)
        self.publish_pouch_date_entry.grid(row=0, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Style:").grid(row=1, column=0, sticky='w', pady=2)
        self.publish_style_combo = ttk.Combobox(form_frame, width=27, values=[
            'pure', 'rustic', 'rustic_experimental', 'other'
        ])
        self.publish_style_combo.grid(row=1, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Water:").grid(row=1, column=2, sticky='w', pady=2, padx=(20, 0))
        self.publish_water_entry = ttk.Entry(form_frame, width=30)
        self.publish_water_entry.grid(row=1, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="ABV (%):").grid(row=2, column=0, sticky='w', pady=2)
        self.publish_abv_entry = ttk.Entry(form_frame, width=30)
        self.publish_abv_entry.grid(row=2, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="SMV:").grid(row=2, column=2, sticky='w', pady=2, padx=(20, 0))
        self.publish_smv_entry = ttk.Entry(form_frame, width=30)
        self.publish_smv_entry.grid(row=2, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Batch Size (L):").grid(row=3, column=0, sticky='w', pady=2)
        self.publish_batch_size_entry = ttk.Entry(form_frame, width=30)
        self.publish_batch_size_entry.grid(row=3, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Rice:").grid(row=3, column=2, sticky='w', pady=2, padx=(20, 0))
        self.publish_rice_entry = ttk.Entry(form_frame, width=30)
        self.publish_rice_entry.grid(row=3, column=3, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Description:").grid(row=4, column=0, sticky='w', pady=2)
        self.publish_desc_entry = ttk.Entry(form_frame, width=30)
        self.publish_desc_entry.grid(row=4, column=1, pady=2, padx=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="Add Publish Notes", command=self.add_publish_notes).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_publish_form).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Load Batches", command=self.load_batch_ids).pack(side='left', padx=5)
        
        # Publish notes list
        list_frame = ttk.LabelFrame(publish_frame, text="Current Publish Notes", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for publish notes
        columns = ('Batch ID', 'Pouch Date', 'Style', 'ABV', 'SMV', 'Batch Size', 'Rice')
        self.publish_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.publish_tree.heading(col, text=col)
            self.publish_tree.column(col, width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.publish_tree.yview)
        self.publish_tree.configure(yscrollcommand=scrollbar.set)
        
        self.publish_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def create_formulas_tab(self):
        """Create live formula calculator tab"""
        formulas_frame = ttk.Frame(self.notebook)
        self.notebook.add(formulas_frame, text="Live Calculator")
        
        # Title
        title_label = ttk.Label(formulas_frame, text="Live Brewing Calculator", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Calculator frame
        calc_frame = ttk.LabelFrame(formulas_frame, text="Hydrometer & Brix Calculator", padding=10)
        calc_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Input fields
        ttk.Label(calc_frame, text="Calibrated Hydrometer Temp (°C):").grid(row=0, column=0, sticky='w', pady=5)
        self.calc_calibrated_temp_entry = ttk.Entry(calc_frame, width=20)
        self.calc_calibrated_temp_entry.grid(row=0, column=1, pady=5, padx=(5, 0))
        self.calc_calibrated_temp_entry.insert(0, "20.0")
        
        ttk.Label(calc_frame, text="Measured Temperature (°C):").grid(row=1, column=0, sticky='w', pady=5)
        self.calc_measured_temp_entry = ttk.Entry(calc_frame, width=20)
        self.calc_measured_temp_entry.grid(row=1, column=1, pady=5, padx=(5, 0))
        self.calc_measured_temp_entry.bind('<KeyRelease>', self.calculate_formulas)
        
        ttk.Label(calc_frame, text="Measured Specific Gravity:").grid(row=2, column=0, sticky='w', pady=5)
        self.calc_measured_sg_entry = ttk.Entry(calc_frame, width=20)
        self.calc_measured_sg_entry.grid(row=2, column=1, pady=5, padx=(5, 0))
        self.calc_measured_sg_entry.bind('<KeyRelease>', self.calculate_formulas)
        
        ttk.Label(calc_frame, text="Measured Brix (%):").grid(row=3, column=0, sticky='w', pady=5)
        self.calc_measured_brix_entry = ttk.Entry(calc_frame, width=20)
        self.calc_measured_brix_entry.grid(row=3, column=1, pady=5, padx=(5, 0))
        self.calc_measured_brix_entry.bind('<KeyRelease>', self.calculate_formulas)
        
        # Results frame
        results_frame = ttk.LabelFrame(calc_frame, text="Calculated Results", padding=10)
        results_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=10)
        
        ttk.Label(results_frame, text="Corrected Gravity:").grid(row=0, column=0, sticky='w', pady=2)
        self.calc_corrected_gravity_label = ttk.Label(results_frame, text="", font=('Arial', 10, 'bold'))
        self.calc_corrected_gravity_label.grid(row=0, column=1, sticky='w', pady=2, padx=(10, 0))
        
        ttk.Label(results_frame, text="ABV (%):").grid(row=1, column=0, sticky='w', pady=2)
        self.calc_abv_label = ttk.Label(results_frame, text="", font=('Arial', 10, 'bold'))
        self.calc_abv_label.grid(row=1, column=1, sticky='w', pady=2, padx=(10, 0))
        
        ttk.Label(results_frame, text="SMV:").grid(row=2, column=0, sticky='w', pady=2)
        self.calc_smv_label = ttk.Label(results_frame, text="", font=('Arial', 10, 'bold'))
        self.calc_smv_label.grid(row=2, column=1, sticky='w', pady=2, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(calc_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Save Calculation", command=self.save_calculation).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_calc_form).pack(side='left', padx=5)
        
        # History frame
        history_frame = ttk.LabelFrame(formulas_frame, text="Calculation History", padding=10)
        history_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for calculation history
        columns = ('Date', 'Cal Temp', 'Meas Temp', 'Meas SG', 'Meas Brix', 'Corrected SG', 'ABV%', 'SMV')
        self.calc_history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.calc_history_tree.heading(col, text=col)
            self.calc_history_tree.column(col, width=100)
        
        self.calc_history_tree.pack(fill='both', expand=True)
        
        # Load calculation history
        self.load_calculation_history()
    
    def create_view_data_tab(self):
        """Create data viewing tab"""
        view_frame = ttk.Frame(self.notebook)
        self.notebook.add(view_frame, text="View Data")
        
        # Title
        title_label = ttk.Label(view_frame, text="Database Overview", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(view_frame, text="Database Statistics", padding=10)
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=8, width=80)
        self.stats_text.pack(fill='both', expand=True)
        
        # Buttons
        button_frame = ttk.Frame(view_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Refresh Statistics", command=self.load_statistics).pack(side='left', padx=5)
        ttk.Button(button_frame, text="View All Recipes", command=self.view_all_recipes).pack(side='left', padx=5)
        ttk.Button(button_frame, text="View All Ingredients", command=self.view_all_ingredients).pack(side='left', padx=5)
    
    def create_google_sheets_tab(self):
        """Create Google Sheets sync tab"""
        sheets_frame = ttk.Frame(self.notebook)
        self.notebook.add(sheets_frame, text="Google Sheets Sync")
        
        # Title
        title_label = ttk.Label(sheets_frame, text="Google Sheets Synchronization", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Status frame
        status_frame = ttk.LabelFrame(sheets_frame, text="Sync Status", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.sync_status_label = ttk.Label(status_frame, text="Not connected to Google Sheets", foreground='red')
        self.sync_status_label.pack(pady=5)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(sheets_frame, text="Configuration", padding=10)
        config_frame.pack(fill='x', padx=10, pady=5)
        
        # Spreadsheet ID entry
        ttk.Label(config_frame, text="Spreadsheet ID:").grid(row=0, column=0, sticky='w', pady=2)
        self.spreadsheet_id_entry = ttk.Entry(config_frame, width=50)
        self.spreadsheet_id_entry.grid(row=0, column=1, pady=2, padx=(5, 0))
        
        # Load current spreadsheet ID
        current_id = get_spreadsheet_id()
        if current_id:
            self.spreadsheet_id_entry.insert(0, current_id)
        
        ttk.Button(config_frame, text="Set ID", command=self.set_spreadsheet_id).grid(row=0, column=2, padx=(5, 0))
        
        # Authentication frame
        auth_frame = ttk.LabelFrame(sheets_frame, text="Authentication", padding=10)
        auth_frame.pack(fill='x', padx=10, pady=5)
        
        auth_button_frame = ttk.Frame(auth_frame)
        auth_button_frame.pack()
        
        ttk.Button(auth_button_frame, text="Authenticate", command=self.authenticate_google_sheets).pack(side='left', padx=5)
        ttk.Button(auth_button_frame, text="Test Connection", command=self.test_google_sheets_connection).pack(side='left', padx=5)
        ttk.Button(auth_button_frame, text="Setup Instructions", command=self.show_setup_instructions).pack(side='left', padx=5)
        
        # Sync operations frame
        sync_frame = ttk.LabelFrame(sheets_frame, text="Synchronization", padding=10)
        sync_frame.pack(fill='x', padx=10, pady=5)
        
        sync_button_frame = ttk.Frame(sync_frame)
        sync_button_frame.pack()
        
        ttk.Button(sync_button_frame, text="Export to Google Sheets", command=self.export_to_google_sheets).pack(side='left', padx=5)
        ttk.Button(sync_button_frame, text="Import from Google Sheets", command=self.import_from_google_sheets).pack(side='left', padx=5)
        ttk.Button(sync_button_frame, text="Open Spreadsheet", command=self.open_google_spreadsheet).pack(side='left', padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(sheets_frame, text="Progress", padding=10)
        progress_frame.pack(fill='x', padx=10, pady=5)
        
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill='x', pady=5)
        
        # Initialize Google Sheets sync
        self.google_sync = GoogleSheetsSync()
    
    def load_ingredients(self):
        """Load ingredients into comboboxes"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT ingredientID, ingredient_type FROM ingredients ORDER BY ingredient_type, ingredientID")
        ingredients = cursor.fetchall()
        
        # Update comboboxes
        ingredient_list = [f"{row[0]} ({row[1]})" for row in ingredients]
        
        # Update recipe comboboxes
        # Rice can be used for both koji and kake
        rice_ingredients = [row[0] for row in ingredients if row[1] == 'rice']
        self.recipe_kake_combo['values'] = rice_ingredients
        self.recipe_koji_combo['values'] = rice_ingredients
        self.recipe_yeast_combo['values'] = [row[0] for row in ingredients if row[1] == 'yeast']
        
        # Update starter comboboxes
        # Rice can be used for both koji and kake
        self.starter_kake_combo['values'] = rice_ingredients
        self.starter_koji_combo['values'] = rice_ingredients
        self.starter_yeast_combo['values'] = [row[0] for row in ingredients if row[1] == 'yeast']
        
        # Update water type combobox
        self.starter_water_combo['values'] = [row[0] for row in ingredients if row[1] == 'water']
        
        # Load ingredients tree
        self.ingredients_tree.delete(*self.ingredients_tree.get_children())
        for row in ingredients:
            cursor.execute("SELECT * FROM ingredients WHERE ingredientID = ?", (row[0],))
            ingredient = cursor.fetchone()
            self.ingredients_tree.insert('', 'end', values=(
                ingredient['ingredientID'],
                ingredient['ingredient_type'],
                ingredient['description'],
                ingredient['source'] or '',
                ingredient['acc_date'] or ''
            ))
    
    def load_starter_data(self):
        """Load batch IDs and ingredients for starters"""
        cursor = self.conn.cursor()
        
        # Load batch IDs
        cursor.execute("SELECT batchID FROM recipe ORDER BY batchID")
        batch_ids = [row[0] for row in cursor.fetchall()]
        self.starter_batch_id_combo['values'] = batch_ids
        
        # Load ingredients
        self.load_ingredients()
        
        # Load starters tree
        self.starters_tree.delete(*self.starters_tree.get_children())
        cursor.execute("SELECT * FROM starters ORDER BY date DESC")
        starters = cursor.fetchall()
        for starter in starters:
            self.starters_tree.insert('', 'end', values=(
                starter['date'] or '',
                starter['starter_batch'] or '',
                starter['batchID'] or '',
                starter['amt_kake'] or '',
                starter['amt_koji'] or '',
                starter['amt_water'] or '',
                starter['yeast'] or '',
                starter['temp_C'] or ''
            ))
    
    def load_batch_ids(self):
        """Load batch IDs for publish notes"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT batchID FROM recipe ORDER BY batchID")
        batch_ids = [row[0] for row in cursor.fetchall()]
        self.publish_batch_id_combo['values'] = batch_ids
        
        # Load publish notes tree
        self.publish_tree.delete(*self.publish_tree.get_children())
        cursor.execute("SELECT * FROM publish_notes ORDER BY batchID")
        notes = cursor.fetchall()
        for note in notes:
            self.publish_tree.insert('', 'end', values=(
                note['batchID'] or '',
                note['pouch_date'] or '',
                note['style'] or '',
                note['abv'] or '',
                note['smv'] or '',
                note['batch_size_l'] or '',
                note['rice'] or ''
            ))
    
    def load_statistics(self):
        """Load database statistics"""
        cursor = self.conn.cursor()
        
        stats = []
        stats.append("=== SakeMonkey Recipe Database Statistics ===\n")
        
        # Count records
        tables = ['ingredients', 'recipe', 'starters', 'publish_notes', 'formulas']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats.append(f"{table.capitalize()}: {count} records")
        
        stats.append("\n=== Ingredients by Type ===")
        cursor.execute("SELECT ingredient_type, COUNT(*) FROM ingredients GROUP BY ingredient_type")
        for row in cursor.fetchall():
            stats.append(f"{row[0]}: {row[1]} items")
        
        stats.append("\n=== Recipe Styles ===")
        cursor.execute("SELECT style, COUNT(*) FROM recipe GROUP BY style")
        for row in cursor.fetchall():
            stats.append(f"{row[0]}: {row[1]} batches")
        
        stats.append("\n=== Recent Recipes ===")
        cursor.execute("SELECT batchID, style, start_date FROM recipe ORDER BY start_date DESC LIMIT 5")
        for row in cursor.fetchall():
            stats.append(f"{row[0]}: {row[1]} style (started: {row[2] or 'N/A'})")
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, '\n'.join(stats))
    
    def add_ingredient(self):
        """Add new ingredient"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO ingredients (ingredientID, ingredient_type, acc_date, source, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.ingredient_id_entry.get(),
                self.ingredient_type_combo.get(),
                self.ingredient_date_entry.get(),
                self.ingredient_source_entry.get(),
                self.ingredient_desc_entry.get()
            ))
            self.conn.commit()
            messagebox.showinfo("Success", "Ingredient added successfully!")
            self.clear_ingredient_form()
            self.load_ingredients()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Ingredient ID already exists!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add ingredient: {str(e)}")
    
    def add_recipe(self):
        """Add new recipe"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO recipe (batchID, batch, style, kake, koji, yeast, starter, 
                                   water_type, start_date, pouch_date, total_kake_g, total_koji_g, 
                                   total_water_mL, ferment_temp_C, addition1_notes, addition2_notes, 
                                   addition3_notes, final_measured_temp_C, final_measured_gravity, 
                                   final_measured_brix, clarified, pasteurized)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.recipe_batch_id_entry.get(),
                self.recipe_batch_entry.get(),
                self.recipe_style_combo.get(),
                self.recipe_kake_combo.get(),
                self.recipe_koji_combo.get(),
                self.recipe_yeast_combo.get(),
                self.recipe_starter_entry.get(),
                self.recipe_water_combo.get(),
                self.recipe_start_date_entry.get(),
                self.recipe_pouch_date_entry.get(),
                self.recipe_total_kake_entry.get(),
                self.recipe_total_koji_entry.get(),
                self.recipe_total_water_entry.get(),
                self.recipe_ferment_temp_entry.get(),
                self.recipe_addition1_entry.get(),
                self.recipe_addition2_entry.get(),
                self.recipe_addition3_entry.get(),
                self.recipe_final_temp_entry.get(),
                self.recipe_final_gravity_entry.get(),
                self.recipe_final_brix_entry.get(),
                self.recipe_clarified_var.get(),
                self.recipe_pasteurized_var.get()
            ))
            self.conn.commit()
            messagebox.showinfo("Success", "Recipe added successfully!")
            self.clear_recipe_form()
            self.load_recipes()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Batch ID already exists!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add recipe: {str(e)}")
    
    def add_starter(self):
        """Add new starter"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO starters (date, starter_batch, batchID, amt_kake, amt_koji, amt_water, 
                                     water_type, kake, koji, yeast, lactic_acid, MgSO4, KCl, temp_C)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.starter_date_entry.get(),
                self.starter_batch_entry.get(),
                self.starter_batch_id_combo.get(),
                self.starter_amt_kake_entry.get(),
                self.starter_amt_koji_entry.get(),
                self.starter_amt_water_entry.get(),
                self.starter_water_combo.get(),
                self.starter_kake_combo.get(),
                self.starter_koji_combo.get(),
                self.starter_yeast_combo.get(),
                self.starter_lactic_acid_entry.get(),
                self.starter_mgso4_entry.get(),
                self.starter_kcl_entry.get(),
                self.starter_temp_entry.get()
            ))
            self.conn.commit()
            messagebox.showinfo("Success", "Starter added successfully!")
            self.clear_starter_form()
            self.load_starter_data()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add starter: {str(e)}")
    
    def add_publish_notes(self):
        """Add publish notes"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO publish_notes 
                (batchID, pouch_date, style, water, abv, smv, batch_size_l, rice, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.publish_batch_id_combo.get(),
                self.publish_pouch_date_entry.get(),
                self.publish_style_combo.get(),
                self.publish_water_entry.get(),
                self.publish_abv_entry.get(),
                self.publish_smv_entry.get(),
                self.publish_batch_size_entry.get(),
                self.publish_rice_entry.get(),
                self.publish_desc_entry.get()
            ))
            self.conn.commit()
            messagebox.showinfo("Success", "Publish notes added successfully!")
            self.clear_publish_form()
            self.load_batch_ids()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add publish notes: {str(e)}")
    
    def clear_ingredient_form(self):
        """Clear ingredient form"""
        self.ingredient_id_entry.delete(0, tk.END)
        self.ingredient_type_combo.set('')
        self.ingredient_desc_entry.delete(0, tk.END)
        self.ingredient_source_entry.delete(0, tk.END)
        self.ingredient_date_entry.delete(0, tk.END)
        self.ingredient_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
    
    def clear_recipe_form(self):
        """Clear recipe form"""
        self.recipe_batch_id_entry.delete(0, tk.END)
        self.recipe_batch_entry.delete(0, tk.END)
        self.recipe_style_combo.set('')
        self.recipe_water_combo.set('')
        self.recipe_kake_combo.set('')
        self.recipe_koji_combo.set('')
        self.recipe_yeast_combo.set('')
        self.recipe_starter_entry.delete(0, tk.END)
        self.recipe_start_date_entry.delete(0, tk.END)
        self.recipe_start_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.recipe_pouch_date_entry.delete(0, tk.END)
        self.recipe_total_kake_entry.delete(0, tk.END)
        self.recipe_total_koji_entry.delete(0, tk.END)
        self.recipe_total_water_entry.delete(0, tk.END)
        self.recipe_ferment_temp_entry.delete(0, tk.END)
        self.recipe_addition1_entry.delete(0, tk.END)
        self.recipe_addition2_entry.delete(0, tk.END)
        self.recipe_addition3_entry.delete(0, tk.END)
        self.recipe_final_temp_entry.delete(0, tk.END)
        self.recipe_final_gravity_entry.delete(0, tk.END)
        self.recipe_final_brix_entry.delete(0, tk.END)
        self.recipe_clarified_var.set(False)
        self.recipe_pasteurized_var.set(False)
    
    def calculate_formulas(self, event=None):
        """Calculate corrected gravity, ABV, and SMV"""
        try:
            # Get input values
            calibrated_temp = float(self.calc_calibrated_temp_entry.get() or 20.0)
            measured_temp = float(self.calc_measured_temp_entry.get() or 0)
            measured_sg = float(self.calc_measured_sg_entry.get() or 0)
            measured_brix = float(self.calc_measured_brix_entry.get() or 0)
            
            if measured_temp == 0 or measured_sg == 0 or measured_brix == 0:
                # Clear results if any required field is empty
                self.calc_corrected_gravity_label.config(text="")
                self.calc_abv_label.config(text="")
                self.calc_smv_label.config(text="")
                return
            
            # Calculate corrected gravity using temperature correction formula
            # Formula: corrected_gravity = measured_gravity * (density_at_measured_temp / density_at_calibrated_temp)
            mt = measured_temp
            mg = measured_sg
            ct = calibrated_temp
            
            # Density calculation at measured temperature
            pmt = 0.999005559846799 - 0.000020305299748608*mt + 0.0000058871378337408*mt**2 - 0.00000001357811768736*mt**3
            
            # Density calculation at calibrated temperature
            pct = 0.999005559846799 - 0.000020305299748608*ct + 0.0000058871378337408*ct**2 - 0.00000001357811768736*ct**3
            
            corrected_gravity = round(mg * pmt / pct, 4)
            
            # Calculate ABV using corrected gravity and brix
            b = measured_brix
            fg = corrected_gravity
            abv = round(1.646*b - 2.703*(145 - 145/fg) - 1.794, 1)
            
            # Calculate SMV using corrected gravity
            smv = round(1443/fg - 1443, 1)
            
            # Update labels
            self.calc_corrected_gravity_label.config(text=f"{corrected_gravity}")
            self.calc_abv_label.config(text=f"{abv}%")
            self.calc_smv_label.config(text=f"{smv}")
            
        except (ValueError, ZeroDivisionError):
            # Clear results if calculation fails
            self.calc_corrected_gravity_label.config(text="")
            self.calc_abv_label.config(text="")
            self.calc_smv_label.config(text="")
    
    def save_calculation(self):
        """Save calculation to database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO formulas (calibrated_temp_c, measured_temp_c, measured_sg, measured_brix, 
                                     corrected_gravity, calculated_abv, calculated_smv)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.calc_calibrated_temp_entry.get(),
                self.calc_measured_temp_entry.get(),
                self.calc_measured_sg_entry.get(),
                self.calc_measured_brix_entry.get(),
                self.calc_corrected_gravity_label.cget("text") if self.calc_corrected_gravity_label.cget("text") else None,
                self.calc_abv_label.cget("text").replace("%", "") if self.calc_abv_label.cget("text") else None,
                self.calc_smv_label.cget("text") if self.calc_smv_label.cget("text") else None
            ))
            self.conn.commit()
            messagebox.showinfo("Success", "Calculation saved successfully!")
            self.load_calculation_history()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save calculation: {str(e)}")
    
    def clear_calc_form(self):
        """Clear calculator form"""
        self.calc_calibrated_temp_entry.delete(0, tk.END)
        self.calc_calibrated_temp_entry.insert(0, "20.0")
        self.calc_measured_temp_entry.delete(0, tk.END)
        self.calc_measured_sg_entry.delete(0, tk.END)
        self.calc_measured_brix_entry.delete(0, tk.END)
        self.calc_corrected_gravity_label.config(text="")
        self.calc_abv_label.config(text="")
        self.calc_smv_label.config(text="")
    
    def load_calculation_history(self):
        """Load calculation history from database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM formulas ORDER BY created_at DESC")
            calculations = cursor.fetchall()
            
            self.calc_history_tree.delete(*self.calc_history_tree.get_children())
            for calc in calculations:
                self.calc_history_tree.insert('', 'end', values=(
                    calc['created_at'][:10] if calc['created_at'] else '',
                    calc['calibrated_temp_c'] or '',
                    calc['measured_temp_c'] or '',
                    calc['measured_sg'] or '',
                    calc['measured_brix'] or '',
                    calc['corrected_gravity'] or '',
                    f"{calc['calculated_abv']}%" if calc['calculated_abv'] else '',
                    calc['calculated_smv'] or ''
                ))
        except Exception as e:
            print(f"Error loading calculation history: {e}")
    
    def clear_starter_form(self):
        """Clear starter form"""
        self.starter_date_entry.delete(0, tk.END)
        self.starter_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.starter_batch_entry.delete(0, tk.END)
        self.starter_batch_id_combo.set('')
        self.starter_water_combo.set('')
        self.starter_amt_kake_entry.delete(0, tk.END)
        self.starter_amt_koji_entry.delete(0, tk.END)
        self.starter_amt_water_entry.delete(0, tk.END)
        self.starter_kake_combo.set('')
        self.starter_koji_combo.set('')
        self.starter_yeast_combo.set('')
        self.starter_lactic_acid_entry.delete(0, tk.END)
        self.starter_mgso4_entry.delete(0, tk.END)
        self.starter_kcl_entry.delete(0, tk.END)
        self.starter_temp_entry.delete(0, tk.END)
    
    def clear_publish_form(self):
        """Clear publish form"""
        self.publish_batch_id_combo.set('')
        self.publish_pouch_date_entry.delete(0, tk.END)
        self.publish_style_combo.set('')
        self.publish_water_entry.delete(0, tk.END)
        self.publish_abv_entry.delete(0, tk.END)
        self.publish_smv_entry.delete(0, tk.END)
        self.publish_batch_size_entry.delete(0, tk.END)
        self.publish_rice_entry.delete(0, tk.END)
        self.publish_desc_entry.delete(0, tk.END)
    
    def load_recipes(self):
        """Load recipes into tree"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT batchID, batch, style, start_date, pouch_date, abv, smv, 
                   clarified, pasteurized, total_kake_g, total_koji_g
            FROM recipe ORDER BY batchID DESC
        """)
        recipes = cursor.fetchall()
        
        self.recipes_tree.delete(*self.recipes_tree.get_children())
        for recipe in recipes:
            # Determine status based on available data
            status = "Planning"
            if recipe['start_date']:
                status = "Started"
            if recipe['pouch_date']:
                status = "Completed"
            if recipe['clarified']:
                status += " (Clarified)"
            if recipe['pasteurized']:
                status += " (Pasteurized)"
            
            # Format ABV and SMV
            abv_text = f"{recipe['abv']:.1f}%" if recipe['abv'] else ""
            smv_text = f"{recipe['smv']:.1f}" if recipe['smv'] else ""
            
            self.recipes_tree.insert('', 'end', values=(
                recipe['batchID'] or '',
                recipe['batch'] or '',
                recipe['style'] or '',
                recipe['start_date'] or '',
                recipe['pouch_date'] or '',
                abv_text,
                smv_text,
                status
            ))
    
    def view_all_recipes(self):
        """View all recipes in a new window"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT r.batchID, r.batch, r.style, r.start_date, r.pouch_date,
                   pn.abv, pn.smv, pn.batch_size_l
            FROM recipe r
            LEFT JOIN publish_notes pn ON r.batchID = pn.batchID
            ORDER BY r.batchID
        """)
        recipes = cursor.fetchall()
        
        # Create new window
        window = tk.Toplevel(self.root)
        window.title("All Recipes")
        window.geometry("800x600")
        
        # Create treeview
        columns = ('Batch ID', 'Batch', 'Style', 'Start Date', 'Pouch Date', 'ABV', 'SMV', 'Size (L)')
        tree = ttk.Treeview(window, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        for recipe in recipes:
            tree.insert('', 'end', values=(
                recipe['batchID'],
                recipe['batch'],
                recipe['style'],
                recipe['start_date'] or '',
                recipe['pouch_date'] or '',
                recipe['abv'] or '',
                recipe['smv'] or '',
                recipe['batch_size_l'] or ''
            ))
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
    
    def view_all_ingredients(self):
        """View all ingredients in a new window"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM ingredients ORDER BY ingredient_type, ingredientID")
        ingredients = cursor.fetchall()
        
        # Create new window
        window = tk.Toplevel(self.root)
        window.title("All Ingredients")
        window.geometry("600x400")
        
        # Create treeview
        columns = ('ID', 'Type', 'Description', 'Source', 'Date')
        tree = ttk.Treeview(window, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        for ingredient in ingredients:
            tree.insert('', 'end', values=(
                ingredient['ingredientID'],
                ingredient['ingredient_type'],
                ingredient['description'],
                ingredient['source'] or '',
                ingredient['acc_date'] or ''
            ))
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
    
    def set_spreadsheet_id(self):
        """Set the Google Spreadsheet ID"""
        spreadsheet_id = self.spreadsheet_id_entry.get().strip()
        if spreadsheet_id:
            set_spreadsheet_id(spreadsheet_id)
            self.google_sync.set_spreadsheet_id(spreadsheet_id)
            messagebox.showinfo("Success", f"Spreadsheet ID set to: {spreadsheet_id}")
        else:
            messagebox.showerror("Error", "Please enter a valid Spreadsheet ID")
    
    def authenticate_google_sheets(self):
        """Authenticate with Google Sheets API"""
        def auth_thread():
            try:
                self.progress_var.set("Authenticating...")
                self.progress_bar.start()
                
                if self.google_sync.authenticate():
                    self.sync_status_label.config(text="Connected to Google Sheets", foreground='green')
                    self.progress_var.set("Authentication successful!")
                else:
                    self.sync_status_label.config(text="Authentication failed", foreground='red')
                    self.progress_var.set("Authentication failed!")
                
            except Exception as e:
                self.sync_status_label.config(text=f"Error: {str(e)}", foreground='red')
                self.progress_var.set(f"Error: {str(e)}")
            finally:
                self.progress_bar.stop()
        
        threading.Thread(target=auth_thread, daemon=True).start()
    
    def test_google_sheets_connection(self):
        """Test Google Sheets connection"""
        def test_thread():
            try:
                self.progress_var.set("Testing connection...")
                self.progress_bar.start()
                
                if self.google_sync.service:
                    sheets = self.google_sync.list_sheets()
                    if sheets:
                        self.sync_status_label.config(text=f"Connected - {len(sheets)} sheets found", foreground='green')
                        self.progress_var.set(f"Connection successful! Found {len(sheets)} sheets")
                    else:
                        self.sync_status_label.config(text="Connected but no sheets found", foreground='orange')
                        self.progress_var.set("Connected but no sheets found")
                else:
                    self.sync_status_label.config(text="Not authenticated", foreground='red')
                    self.progress_var.set("Not authenticated")
                
            except Exception as e:
                self.sync_status_label.config(text=f"Connection failed: {str(e)}", foreground='red')
                self.progress_var.set(f"Connection failed: {str(e)}")
            finally:
                self.progress_bar.stop()
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def show_setup_instructions(self):
        """Show Google Sheets setup instructions"""
        instructions = """
Google Sheets API Setup Instructions:

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project or select an existing one
3. Enable the Google Sheets API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Download the JSON file
   - Rename it to 'credentials.json' and place in this directory
5. Set your spreadsheet ID in the configuration above
6. Click "Authenticate" to complete setup

Your spreadsheet should have these sheets:
- Ingredients
- Recipe  
- Starters
- PublishNotes
- Formulas
        """
        
        # Create new window for instructions
        window = tk.Toplevel(self.root)
        window.title("Google Sheets Setup Instructions")
        window.geometry("600x500")
        
        text_widget = tk.Text(window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert(1.0, instructions)
        text_widget.config(state=tk.DISABLED)
    
    def export_to_google_sheets(self):
        """Export database to Google Sheets"""
        def export_thread():
            try:
                self.progress_var.set("Exporting to Google Sheets...")
                self.progress_bar.start()
                
                if not self.google_sync.service:
                    self.progress_var.set("Not authenticated. Please authenticate first.")
                    return
                
                if self.google_sync.export_to_sheets():
                    self.progress_var.set("Export completed successfully!")
                    messagebox.showinfo("Success", "Database exported to Google Sheets successfully!")
                else:
                    self.progress_var.set("Export failed!")
                    messagebox.showerror("Error", "Failed to export to Google Sheets")
                
            except Exception as e:
                self.progress_var.set(f"Export error: {str(e)}")
                messagebox.showerror("Error", f"Export failed: {str(e)}")
            finally:
                self.progress_bar.stop()
        
        threading.Thread(target=export_thread, daemon=True).start()
    
    def import_from_google_sheets(self):
        """Import database from Google Sheets"""
        def import_thread():
            try:
                self.progress_var.set("Importing from Google Sheets...")
                self.progress_bar.start()
                
                if not self.google_sync.service:
                    self.progress_var.set("Not authenticated. Please authenticate first.")
                    return
                
                # Ask for confirmation
                if messagebox.askyesno("Confirm Import", 
                                     "This will replace all data in your local database with data from Google Sheets. Continue?"):
                    if self.google_sync.import_from_sheets():
                        self.progress_var.set("Import completed successfully!")
                        messagebox.showinfo("Success", "Database imported from Google Sheets successfully!")
                        # Refresh all data in GUI
                        self.load_ingredients()
                        self.load_recipes()
                        self.load_starter_data()
                        self.load_batch_ids()
                        self.load_statistics()
                    else:
                        self.progress_var.set("Import failed!")
                        messagebox.showerror("Error", "Failed to import from Google Sheets")
                
            except Exception as e:
                self.progress_var.set(f"Import error: {str(e)}")
                messagebox.showerror("Error", f"Import failed: {str(e)}")
            finally:
                self.progress_bar.stop()
        
        threading.Thread(target=import_thread, daemon=True).start()
    
    def open_google_spreadsheet(self):
        """Open Google Spreadsheet in browser"""
        if self.google_sync.spreadsheet_id:
            import webbrowser
            url = self.google_sync.get_spreadsheet_url()
            webbrowser.open(url)
        else:
            messagebox.showerror("Error", "No spreadsheet ID set")
    
    def __del__(self):
        """Cleanup database connection"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

def main():
    """Main function to run the GUI application"""
    root = tk.Tk()
    app = SakeRecipeGUI(root)
    
    # Load initial data
    app.load_recipes()
    app.load_starter_data()
    app.load_batch_ids()
    app.load_statistics()
    
    root.mainloop()

if __name__ == "__main__":
    main()
