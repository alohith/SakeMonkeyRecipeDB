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
        self.create_view_data_tab()
    
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
            'yeast', 'koji_rice', 'kake_rice', 'rice', 'nutrientMix', 'water', 'other'
        ])
        self.ingredient_type_combo.grid(row=1, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky='w', pady=2)
        self.ingredient_desc_entry = ttk.Entry(form_frame, width=30)
        self.ingredient_desc_entry.grid(row=2, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Source:").grid(row=3, column=0, sticky='w', pady=2)
        self.ingredient_source_entry = ttk.Entry(form_frame, width=30)
        self.ingredient_source_entry.grid(row=3, column=1, pady=2, padx=(5, 0))
        
        ttk.Label(form_frame, text="Access Date:").grid(row=4, column=0, sticky='w', pady=2)
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
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="Add Recipe", command=self.add_recipe).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_recipe_form).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Load Ingredients", command=self.load_ingredients).pack(side='left', padx=5)
        
        # Recipes list
        list_frame = ttk.LabelFrame(recipes_frame, text="Current Recipes", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for recipes
        columns = ('Batch ID', 'Batch', 'Style', 'Kake', 'Koji', 'Yeast', 'Water', 'Start Date')
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
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="Add Starter", command=self.add_starter).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_starter_form).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Load Data", command=self.load_starter_data).pack(side='left', padx=5)
        
        # Starters list
        list_frame = ttk.LabelFrame(starters_frame, text="Current Starters", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for starters
        columns = ('Date', 'Starter Batch', 'Batch ID', 'Amt Kake', 'Amt Koji', 'Amt Water', 'Yeast')
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
    
    def load_ingredients(self):
        """Load ingredients into comboboxes"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT ingredientID, ingredient_type FROM ingredients ORDER BY ingredient_type, ingredientID")
        ingredients = cursor.fetchall()
        
        # Update comboboxes
        ingredient_list = [f"{row[0]} ({row[1]})" for row in ingredients]
        
        # Update recipe comboboxes
        self.recipe_kake_combo['values'] = [row[0] for row in ingredients if 'rice' in row[1]]
        self.recipe_koji_combo['values'] = [row[0] for row in ingredients if 'koji' in row[1]]
        self.recipe_yeast_combo['values'] = [row[0] for row in ingredients if row[1] == 'yeast']
        
        # Update starter comboboxes
        self.starter_kake_combo['values'] = [row[0] for row in ingredients if 'rice' in row[1]]
        self.starter_koji_combo['values'] = [row[0] for row in ingredients if 'koji' in row[1]]
        self.starter_yeast_combo['values'] = [row[0] for row in ingredients if row[1] == 'yeast']
        
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
                starter['yeast'] or ''
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
                                   water_type, start_date, pouch_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                self.recipe_pouch_date_entry.get()
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
                                     water_type, kake, koji, yeast)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                self.starter_yeast_combo.get()
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
            SELECT batchID, batch, style, kake, koji, yeast, water_type, start_date
            FROM recipe ORDER BY batchID
        """)
        recipes = cursor.fetchall()
        
        self.recipes_tree.delete(*self.recipes_tree.get_children())
        for recipe in recipes:
            self.recipes_tree.insert('', 'end', values=(
                recipe['batchID'],
                recipe['batch'],
                recipe['style'],
                recipe['kake'],
                recipe['koji'],
                recipe['yeast'],
                recipe['water_type'],
                recipe['start_date'] or ''
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
