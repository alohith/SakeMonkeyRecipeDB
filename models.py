"""
Database models for SakeMonkey Recipe Database
Using SQLModel for type-safe database operations
"""
from datetime import date
from typing import Optional
from sqlmodel import SQLModel, Field, Column, String, Integer, Float, Boolean, Date
from enum import Enum


class StyleEnum(str, Enum):
    """Sake style categories"""
    PURE = "pure"
    RUSTIC = "rustic"
    RUSTIC_EXPERIMENTAL = "rustic_experimental"


class IngredientTypeEnum(str, Enum):
    """Ingredient type categories"""
    RICE = "rice"
    KAKI_RICE = "kake_rice"
    KOJI_RICE = "koji_rice"
    YEAST = "yeast"
    WATER = "water"


class Ingredient(SQLModel, table=True):
    """Ingredients table"""
    __tablename__ = "ingredients"
    
    #ID: Optional[int] = Field(default=None, primary_key=True)
    ingredientID: Optional[str] = Field(default=None, sa_column=Column("ingredientID", String, primary_key=True))  # IngredientID name from Google Sheet
    ingredient_type: str = Field(sa_column=Column(String))
    acc_date: Optional[date] = Field(default=None, sa_column=Column(Date))
    source: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)


class Starter(SQLModel, table=True):
    """Starters table"""
    __tablename__ = "starters"
    
    #StarterBatch: Optional[int] = Field(default=None, primary_key=True)
    StarterBatch: Optional[str] = Field(default=None, sa_column=Column("StarterBatch", String, primary_key=True))  # StarterBatchID name from Google Sheet
    Date: Optional[date] = Field(default=None, sa_column=Column(Date))
    BatchID: Optional[str] = Field(default=None, index=True)
    Amt_Kake: Optional[float] = Field(default=None)  # grams
    Amt_Koji: Optional[float] = Field(default=None)  # grams
    Amt_water: Optional[float] = Field(default=None)  # ml
    water_type: Optional[str] = Field(default=None, foreign_key="ingredients.ingredientID")
    Kake: Optional[str] = Field(default=None, foreign_key="ingredients.ingredientID")
    Koji: Optional[str] = Field(default=None, foreign_key="ingredients.ingredientID")
    yeast: Optional[str] = Field(default=None, foreign_key="ingredients.ingredientID")
    lactic_acid: Optional[float] = Field(default=None)  # grams
    MgSO4: Optional[float] = Field(default=None)  # grams
    KCl: Optional[float] = Field(default=None)  # grams
    temp_C: Optional[float] = Field(default=None)  # temperature in C


class Recipe(SQLModel, table=True):
    """Recipe table - main batch tracking"""
    __tablename__ = "recipe"
    
    batchID: Optional[str] = Field(default=None, primary_key=True)
    start_date: Optional[date] = Field(default=None, sa_column=Column(Date))
    pouch_date: Optional[date] = Field(default=None, sa_column=Column(Date))
    batch: Optional[int] = Field(default=None)  # increment on batch made
    style: Optional[str] = Field(default=None)  # pure, rustic, rustic_experimental
    kake: Optional[str] = Field(default=None, foreign_key="ingredients.ingredientID")
    koji: Optional[str] = Field(default=None, foreign_key="ingredients.ingredientID")
    yeast: Optional[str] = Field(default=None, foreign_key="ingredients.ingredientID")
    starter: Optional[str] = Field(default=None, foreign_key="starters.StarterBatch")
    water_type: Optional[str] = Field(default=None, foreign_key="ingredients.ingredientID")
    total_kake_g: Optional[float] = Field(default=None)  # running total in grams
    total_koji_g: Optional[float] = Field(default=None)  # running total in grams
    total_water_mL: Optional[float] = Field(default=None)  # running total in ml
    ferment_temp_C: Optional[float] = Field(default=None)  # temperature in C
    Addition1_Notes: Optional[str] = Field(default=None)
    Addition2_Notes: Optional[str] = Field(default=None)
    Addition3_Notes: Optional[str] = Field(default=None)
    ferment_finish_gravity: Optional[float] = Field(default=None)
    ferment_finish_brix: Optional[float] = Field(default=None)
    final_measured_temp_C: Optional[float] = Field(default=None)  # temperature in C
    final_measured_gravity: Optional[float] = Field(default=None)
    final_measured_Brix_pct: Optional[float] = Field(default=None)
    final_gravity: Optional[float] = Field(default=None)  # calculated
    ABV_pct: Optional[float] = Field(default=None)  # calculated
    SMV: Optional[float] = Field(default=None)  # calculated
    final_water_addition_mL: Optional[float] = Field(default=None)
    clarified: Optional[bool] = Field(default=False)
    pasteurized: Optional[bool] = Field(default=False)
    pasteurization_notes: Optional[str] = Field(default=None)
    finishing_additions: Optional[str] = Field(default=None)


class PublishNote(SQLModel, table=True):
    """PublishNotes table - public-facing product information"""
    __tablename__ = "publishnotes"
    
    BatchID: str = Field(default=None, primary_key=True, foreign_key="recipe.batchID")
    Pouch_Date: Optional[date] = Field(default=None, sa_column=Column(Date))
    Style: Optional[str] = Field(default=None)
    Water: Optional[str] = Field(default=None, foreign_key="ingredients.ingredientID")
    ABV: Optional[float] = Field(default=None)
    SMV: Optional[float] = Field(default=None)
    Batch_Size_L: Optional[float] = Field(default=None)
    Rice: Optional[str] = Field(default=None)
    Description: Optional[str] = Field(default=None)

