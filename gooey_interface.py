"""
Gooey-based data entry + calculator interface for the SakeMonkey database.
This GUI enforces the domain rules defined in rules.txt while remaining
scriptable from the command line.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
import json
from typing import Any, Dict, List, Optional

from gooey import Gooey, GooeyParser
from sqlmodel import select

from database import get_session, init_database
from formulas import (
    calculate_abv,
    calculate_dilution_adjustment,
    calculate_final_gravity,
    calculate_smv,
)
from google_sheets_sync import sync_from_google_sheets, sync_to_google_sheets
from models import (
    Ingredient,
    IngredientTypeEnum,
    PublishNote,
    Recipe,
    Starter,
    StyleEnum,
)


TARGET_PROFILES = {
    "Pure": {"brix": 11.0, "gravity": 1.005},
    "Mixer": {"brix": 12.0, "gravity": 0.995},
}

PLACEHOLDER = "-- select an entry --"
STYLE_PLACEHOLDER = "-- use recipe style --"

MODEL_MAP = {
    "ingredients": Ingredient,
    "recipes": Recipe,
    "starters": Starter,
    "publishnotes": PublishNote,
}

ORDER_BY = {
    "ingredients": Ingredient.ingredientID,
    "recipes": Recipe.start_date,
    "starters": Starter.StarterBatch,
    "publishnotes": PublishNote.Pouch_Date,
}


@dataclass
class ChoiceSet:
    """Holds display labels and the underlying IDs for dropdowns."""

    labels: List[str]
    mapping: Dict[str, Optional[Any]]
    placeholder: str

    def resolve(
        self,
        selection: Optional[str],
        *,
        required: bool,
        label: str,
    ) -> Optional[Any]:
        key = selection or self.placeholder
        if key not in self.mapping:
            raise ValueError(f"{label} selection '{selection}' is not valid.")
        value = self.mapping[key]
        if required and value is None:
            raise ValueError(
                f"A {label} selection is required. Use the Add Ingredient tab to create one if needed."
            )
        return value


def describe_ingredient(ingredient: Ingredient) -> str:
    """Format ingredient display: use IngredientID name from Google Sheet when available"""
    # Priority: ingredientID (from Google Sheet) > source > description > ID
    type_part = f"({ingredient.ingredient_type})"
    
    # Use ingredientID name from Google Sheet if available (e.g., "Prop_sake9")
    if ingredient.ingredientID:
        primary_name = ingredient.ingredientID
        if ingredient.description:
            return f"{primary_name} {type_part} - {ingredient.description}"
        else:
            return f"{primary_name} {type_part}"
    
    # Fallback to source if ingredientID not available
    if ingredient.source:
        if ingredient.description:
            return f"{ingredient.source} {type_part} - {ingredient.description}"
        else:
            return f"{ingredient.source} {type_part}"
    
    # Fallback to description
    if ingredient.description:
        return f"{ingredient.description} {type_part}"
    
    # Final fallback: use numeric ID
    return f"ingredientID {ingredient.ingredientID} {type_part}"


def format_starter_code(value: Optional[Any]) -> str:
    """
    Format starter batch code for display.
    Handles both string values (like "s64", "s100") and numeric values.
    Supports 3+ digit numbers (s100, s101, etc.)
    """
    if value is None:
        return "s??"
    
    # If it's already a string starting with 's', return as-is
    value_str = str(value).strip()
    if value_str.lower().startswith('s'):
        return value_str
    
    # Try to extract numeric value and format
    try:
        # Remove 's' prefix if present
        numeric_str = value_str.lstrip('sS')
        numeric_value = int(numeric_str)
        # Format without zero-padding to support 3+ digits (s64, s100, s101, etc.)
        return f"s{numeric_value}"
    except (ValueError, TypeError):
        # If conversion fails, return as string with 's' prefix if not present
        if not value_str.lower().startswith('s'):
            return f"s{value_str}"
        return value_str


def describe_starter(starter: Starter) -> str:
    """Format starter display using StarterBatchID nomenclature"""
    code = format_starter_code(starter.StarterBatch)
    batch_label = starter.BatchID or "unassigned"
    date_label = starter.Date.isoformat() if isinstance(starter.Date, date) else "no date"
    return f"StarterBatchID {starter.StarterBatch} ({code}) | BatchID {batch_label} | {date_label}"


def build_choice_set(
    records: List[Any],
    *,
    label_func,
    value_func,
    placeholder: str = PLACEHOLDER,
) -> ChoiceSet:
    labels: List[str] = [placeholder]
    mapping: Dict[str, Optional[Any]] = {placeholder: None}

    for record in records:
        label = label_func(record)
        labels.append(label)
        mapping[label] = value_func(record)

    return ChoiceSet(labels=labels, mapping=mapping, placeholder=placeholder)


def build_choice_cache(session) -> Dict[str, ChoiceSet]:
    cache: Dict[str, ChoiceSet] = {}

    rice_types = [IngredientTypeEnum.RICE.value, IngredientTypeEnum.KAKI_RICE.value]
    koji_types = [IngredientTypeEnum.RICE.value, IngredientTypeEnum.KOJI_RICE.value]
    yeast_types = [IngredientTypeEnum.YEAST.value]
    water_types = [IngredientTypeEnum.WATER.value]

    cache["kake"] = build_ingredient_choices(session, rice_types, "kake rice")
    cache["koji"] = build_ingredient_choices(session, koji_types, "koji rice")
    cache["yeast"] = build_ingredient_choices(session, yeast_types, "yeast strain")
    cache["water"] = build_ingredient_choices(session, water_types, "water source")

    # Get all starter records and sort by numeric value of StarterBatch
    # This handles string StarterBatch values like "s64", "s100" correctly
    starter_records = session.exec(select(Starter)).all()
    def sort_key(starter):
        if starter.StarterBatch:
            batch_str = str(starter.StarterBatch).strip().lstrip('sS')
            try:
                return int(batch_str)
            except (ValueError, TypeError):
                return 0
        return 0
    starter_records = sorted(starter_records, key=sort_key)
    
    # Find default Shubo starter (250g Koji, 250ml Water, .4g Lactic Acid at 6C)
    default_shubo = None
    for starter in starter_records:
        if (starter.Amt_Koji == 250.0 and starter.Amt_water == 250.0 and 
            starter.lactic_acid == 0.4 and starter.temp_C == 6.0):
            default_shubo = starter
            break
    
    cache["starter_batches"] = build_choice_set(
        starter_records,
        label_func=describe_starter,
        value_func=lambda s: s.StarterBatch,
        placeholder="Auto-create default Shubo starter",
    )
    # Set default to Shubo starter if found
    if default_shubo:
        shubo_label = describe_starter(default_shubo)
        if shubo_label in cache["starter_batches"].labels:
            cache["starter_batches"].default_label = shubo_label

    return cache


def build_ingredient_choices(session, allowed_types: List[str], label: str) -> ChoiceSet:
    stmt = (
        select(Ingredient)
        .where(Ingredient.ingredient_type.in_(allowed_types))
        .order_by(Ingredient.ingredientID)
    )
    records = session.exec(stmt).all()

    placeholder = f"-- choose {label} --" if records else f"No {label} found (add via Add Ingredient)"
    choice_set = build_choice_set(
        records,
        label_func=describe_ingredient,
        value_func=lambda ingredient: ingredient.ingredientID,
        placeholder=placeholder,
    )
    # Set default to first available ingredient if records exist
    if records and choice_set.labels:
        # First label is placeholder, second is first actual ingredient
        if len(choice_set.labels) > 1:
            choice_set.default_label = choice_set.labels[1]
    return choice_set


def parse_date_value(raw: Optional[str], label: str, *, required: bool = False):
    if not raw:
        if required:
            raise ValueError(f"{label} is required (YYYY-MM-DD).")
        return None

    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"{label} must be a date in YYYY-MM-DD format.")


def parse_float_value(raw: Optional[str], label: str) -> Optional[float]:
    if raw in (None, "", PLACEHOLDER):
        return None
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{label} must be a number.") from exc


def parse_int_value(raw: Optional[str], label: str, *, required: bool = False) -> Optional[int]:
    if raw in (None, "", PLACEHOLDER):
        if required:
            raise ValueError(f"{label} is required.")
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{label} must be an integer.") from exc


def normalize_style(style: Optional[str]) -> Optional[str]:
    """
    Normalize human-readable style names to enum values.
    Examples:
    - "Pure" -> "pure"
    - "Rustic Experimental" -> "rustic_experimental"
    - "rustic_experimental" -> "rustic_experimental"
    - "RUSTIC" -> "rustic"
    """
    if style is None or style == "":
        return None
    
    style_clean = style.strip()
    if not style_clean:
        return None
    
    # Convert to lowercase and replace spaces/hyphens with underscores
    normalized = style_clean.lower().replace(" ", "_").replace("-", "_")
    
    # Map common variations to enum values
    style_mapping = {
        "pure": StyleEnum.PURE.value,
        "rustic": StyleEnum.RUSTIC.value,
        "rustic_experimental": StyleEnum.RUSTIC_EXPERIMENTAL.value,
        "rusticexperimental": StyleEnum.RUSTIC_EXPERIMENTAL.value,  # no underscore
    }
    
    # Check if normalized value matches an enum value
    if normalized in style_mapping:
        return style_mapping[normalized]
    
    # Check if it already matches an enum value
    if normalized in [s.value for s in StyleEnum]:
        return normalized
    
    # Return None if no match (caller can handle validation)
    return None


def format_style_for_display(style: Optional[str]) -> str:
    """
    Convert enum style values to human-readable format for display.
    Examples:
    - "pure" -> "Pure"
    - "rustic_experimental" -> "Rustic Experimental"
    - "rustic" -> "Rustic"
    """
    if style is None or style == "":
        return ""
    
    # Map enum values to human-readable names
    style_display_map = {
        StyleEnum.PURE.value: "Pure",
        StyleEnum.RUSTIC.value: "Rustic",
        StyleEnum.RUSTIC_EXPERIMENTAL.value: "Rustic Experimental",
    }
    
    # Check if it's an enum value
    if style in style_display_map:
        return style_display_map[style]
    
    # If it's already human-readable or custom, return as-is
    return style


def coalesce_text(value: Optional[str]) -> Optional[str]:
    return value.strip() if value and value.strip() else None


def sum_optional(values) -> Optional[float]:
    cleaned = [value for value in values if value is not None]
    return sum(cleaned) if cleaned else None


def record_to_dict(row: Any) -> Dict[str, Any]:
    if hasattr(row, "model_dump"):
        data = row.model_dump(exclude_none=True)
    elif hasattr(row, "dict"):
        data = row.dict()
    else:
        data = {k: v for k, v in row.__dict__.items() if not k.startswith("_")}
    return data


def get_next_starter_batch(session) -> str:
    """
    Get the next starter batch ID.
    Handles string StarterBatch values like "s64", "s100", etc.
    Returns the next sequential value (e.g., "s65" if last was "s64").
    """
    result = session.exec(select(Starter.StarterBatch).order_by(Starter.StarterBatch.desc())).first()
    if not result:
        return "s1"
    
    try:
        # Handle string values like "s64", "s100"
        result_str = str(result).strip()
        if result_str.lower().startswith('s'):
            # Extract numeric part
            numeric_str = result_str.lstrip('sS')
            try:
                numeric_value = int(numeric_str)
                return f"s{numeric_value + 1}"
            except ValueError:
                # If it's not a simple number, try to increment
                pass
        
        # Try to convert to int and increment
        numeric_value = int(result)
        return f"s{numeric_value + 1}"
    except (ValueError, TypeError):
        # Fallback: if we can't parse, return "s1"
        return "s1"


def create_shubo_starter(
    session,
    batch_id: str,
    start_date_value: Optional[date],
    kake_id: Optional[int],
    koji_id: Optional[int],
    yeast_id: Optional[int],
    water_id: Optional[int],
) -> str:
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
        lactic_acid=0.4,  # .4g Lactic Acid as per requirements
        temp_C=6.0,
    )
    session.add(starter)
    session.commit()
    print(
        "No starter provided; created default 'Shubo' starter "
        f"{format_starter_code(starter_batch)} with 250g Koji / 250mL Water / 0.4g Lactic Acid at 6C."
    )
    return starter_batch


def build_parser(choice_cache: Dict[str, ChoiceSet]) -> GooeyParser:
    parser = GooeyParser(
        description=(
            "Use this interface to add ingredients, starters, recipes, publish notes, "
            "and run brewing formulas per the requirements defined in rules.txt."
        )
    )

    subparsers = parser.add_subparsers(help="Select the action you want to perform", dest="command")
    subparsers.required = True

    add_ingredient_parser(subparsers)
    add_recipe_parser(subparsers, choice_cache)
    add_starter_parser(subparsers, choice_cache)
    add_publish_parser(subparsers, choice_cache)
    add_formulas_parser(subparsers)  # Adds both formula-gravity and formula-target
    add_database_view_parser(subparsers)
    add_google_sync_parser(subparsers)

    return parser


def add_ingredient_parser(subparsers):
    parser = subparsers.add_parser("add-ingredient", help="Add a new ingredient record")
    parser.add_argument(
        "--ingredient_type",
        required=True,
        choices=[enum.value for enum in IngredientTypeEnum],
        widget="Dropdown",
        help="Ingredient category. Must match the allowed types referenced in rules.txt.",
    )
    parser.add_argument(
        "--acc_date",
        required=True,
        widget="DateChooser",
        help="Accession date for tracking when the ingredient became available.",
    )
    parser.add_argument(
        "--source",
        help="Supplier or source reference for the ingredient.",
    )
    parser.add_argument(
        "--description",
        help="Short description (variety, milling %, etc.).",
    )


def add_recipe_parser(subparsers, choice_cache: Dict[str, ChoiceSet]):
    parser = subparsers.add_parser("add-recipe", help="Create or update a recipe/batch entry")

    batch_group = parser.add_argument_group("Batch + Schedule")
    batch_group.add_argument(
        "--batch_id",
        required=True,
        help="Unique batchID (ties Recipe, Starter, and PublishNotes together).",
    )
    batch_group.add_argument(
        "--batch_number",
        help="Sequential batch counter (integer). Will be parsed from batchID if not provided.",
    )
    # Add option to create new style
    style_choices = [style.value for style in StyleEnum] + ["-- create new style --"]
    batch_group.add_argument(
        "--style",
        choices=style_choices,
        default=StyleEnum.PURE.value,
        widget="Dropdown",
        help="Recipe style (restricted to allowed values). Select '-- create new style --' to add a new style.",
    )
    batch_group.add_argument(
        "--new_style_name",
        help="New style name (only used if '-- create new style --' is selected).",
    )
    batch_group.add_argument(
        "--start_date",
        required=True,
        widget="DateChooser",
        help="Date the batch started fermenting.",
    )
    batch_group.add_argument(
        "--pouch_date",
        widget="DateChooser",
        help="Date the batch was packaged/pouched.",
    )
    starter_default = getattr(choice_cache["starter_batches"], "default_label", 
                              choice_cache["starter_batches"].placeholder)
    batch_group.add_argument(
        "--starter_batch",
        choices=choice_cache["starter_batches"].labels,
        widget="Dropdown",
        default=starter_default,
        help="StarterBatchID reference (defaults to Shubo starter: 250g Koji, 250ml Water, .4g Lactic Acid at 6C).",
    )

    ingredient_group = parser.add_argument_group("Core Ingredients")
    # Get default values (first available ingredient)
    kake_default = getattr(choice_cache["kake"], "default_label", choice_cache["kake"].placeholder)
    koji_default = getattr(choice_cache["koji"], "default_label", choice_cache["koji"].placeholder)
    yeast_default = getattr(choice_cache["yeast"], "default_label", choice_cache["yeast"].placeholder)
    water_default = getattr(choice_cache["water"], "default_label", choice_cache["water"].placeholder)
    
    ingredient_group.add_argument(
        "--kake",
        choices=choice_cache["kake"].labels,
        widget="FilterableDropdown",
        default=kake_default,
        help="ingredientID for kake rice (must be rice/kake_rice per rules).",
    )
    ingredient_group.add_argument(
        "--koji",
        choices=choice_cache["koji"].labels,
        widget="FilterableDropdown",
        default=koji_default,
        help="ingredientID for koji rice (must be rice/koji_rice per rules).",
    )
    ingredient_group.add_argument(
        "--yeast",
        choices=choice_cache["yeast"].labels,
        widget="FilterableDropdown",
        default=yeast_default,
        help="ingredientID for yeast (must be yeast type).",
    )
    ingredient_group.add_argument(
        "--water_type",
        choices=choice_cache["water"].labels,
        widget="Dropdown",
        default=water_default,
        help="ingredientID for water (spring/distilled/etc.).",
    )

    totals_group = parser.add_argument_group("Totals + Fermentation")
    totals_group.add_argument("--total_kake_g", help="Running total of kake rice in grams.")
    totals_group.add_argument("--total_koji_g", help="Running total of koji rice in grams.")
    totals_group.add_argument("--total_water_ml", help="Running total of water in milliliters.")
    totals_group.add_argument(
        "--ferment_temp_c", 
        default="6",
        help="Fermentation temperature in °C (defaults to 6C).",
    )
    totals_group.add_argument("--addition1_notes", help="Notes for first addition.")
    totals_group.add_argument("--addition2_notes", help="Notes for second addition.")
    totals_group.add_argument("--addition3_notes", help="Notes for third addition.")

    measurement_group = parser.add_argument_group("Measurements + Calculations")
    measurement_group.add_argument("--ferment_finish_gravity", help="Specific gravity at end of ferment.")
    measurement_group.add_argument("--ferment_finish_brix", help="%Brix at end of ferment.")
    measurement_group.add_argument("--final_measured_temp_c", help="Temperature for final measurements (°C).")
    measurement_group.add_argument("--final_measured_gravity", help="Final specific gravity reading.")
    measurement_group.add_argument("--final_measured_brix_pct", help="Final %Brix reading.")
    measurement_group.add_argument(
        "--hydrometer_calibrated_temp",
        help="Hydrometer calibration temperature (default 20C).",
        default="20",
    )
    measurement_group.add_argument(
        "--final_water_addition_ml",
        help="Water added before proofing down (mL).",
    )

    finishing_group = parser.add_argument_group("Processing + Finishing")
    finishing_group.add_argument("--pasteurization_notes", help="Describe pasteurization steps.")
    finishing_group.add_argument("--finishing_additions", help="Final addition notes.")
    finishing_group.add_argument(
        "--clarified",
        action="store_true",
        help="Check if the batch was clarified.",
    )
    finishing_group.add_argument(
        "--pasteurized",
        action="store_true",
        help="Check if the batch was pasteurized.",
    )


def add_starter_parser(subparsers, choice_cache: Dict[str, ChoiceSet]):
    parser = subparsers.add_parser("add-starter", help="Log a new starter build")

    core_group = parser.add_argument_group("Starter Details")
    core_group.add_argument(
        "--starter_batch",
        required=True,
        help="StarterBatch identifier (e.g., s64, s100, or just the number). Supports 3+ digits.",
    )
    core_group.add_argument(
        "--starter_date",
        required=True,
        widget="DateChooser",
        help="Date the starter was created.",
    )
    core_group.add_argument(
        "--batch_id",
        help="BatchID this starter feeds (optional, but recommended).",
    )

    ingredient_group = parser.add_argument_group("Starter Ingredients")
    ingredient_group.add_argument(
        "--kake",
        choices=choice_cache["kake"].labels,
        widget="FilterableDropdown",
        default=choice_cache["kake"].placeholder,
        help="Kake rice ingredient ID for the starter.",
    )
    ingredient_group.add_argument(
        "--koji",
        choices=choice_cache["koji"].labels,
        widget="FilterableDropdown",
        default=choice_cache["koji"].placeholder,
        help="Koji rice ingredient ID for the starter.",
    )
    ingredient_group.add_argument(
        "--yeast",
        choices=choice_cache["yeast"].labels,
        widget="FilterableDropdown",
        default=choice_cache["yeast"].placeholder,
        help="Yeast ingredient ID for the starter.",
    )
    ingredient_group.add_argument(
        "--water_type",
        choices=choice_cache["water"].labels,
        widget="Dropdown",
        default=choice_cache["water"].placeholder,
        help="Water ingredient ID for the starter.",
    )

    amount_group = parser.add_argument_group("Amounts + Chemistry")
    amount_group.add_argument("--amt_kake_g", help="Kake rice in grams.")
    amount_group.add_argument("--amt_koji_g", help="Koji rice in grams.")
    amount_group.add_argument("--amt_water_ml", help="Water in milliliters.")
    amount_group.add_argument("--lactic_acid_g", help="Lactic acid in grams.")
    amount_group.add_argument("--mgso4_g", help="MgSO4 in grams.")
    amount_group.add_argument("--kcl_g", help="KCl in grams.")
    amount_group.add_argument("--starter_temp_c", help="Starter temperature in °C.")


def add_publish_parser(subparsers, choice_cache: Dict[str, ChoiceSet]):
    parser = subparsers.add_parser("add-publish-note", help="Create/update a publish note")

    core_group = parser.add_argument_group("Publish Details")
    # Create human-readable style choices for dropdown
    human_readable_styles = {
        StyleEnum.PURE.value: "Pure",
        StyleEnum.RUSTIC.value: "Rustic",
        StyleEnum.RUSTIC_EXPERIMENTAL.value: "Rustic Experimental",
    }
    style_choices = [STYLE_PLACEHOLDER] + [human_readable_styles.get(s.value, s.value) for s in StyleEnum]
    core_group.add_argument(
        "--batch_id",
        required=True,
        help="BatchID to publish (must exist in recipe table).",
    )
    core_group.add_argument(
        "--pouch_date",
        widget="DateChooser",
        help="Override pouch date (defaults to recipe.pouch_date).",
    )
    core_group.add_argument(
        "--style_override",
        choices=style_choices,
        default=STYLE_PLACEHOLDER,
        widget="Dropdown",
        help="Override style for publish notes (optional). Accepts: Pure, Rustic, Rustic Experimental (or enum values).",
    )
    core_group.add_argument(
        "--water_choice",
        choices=choice_cache["water"].labels,
        widget="Dropdown",
        default=choice_cache["water"].placeholder,
        help="Override water ingredient ID (optional).",
    )
    core_group.add_argument(
        "--description",
        required=True,
        help="Public-facing description/tasting notes.",
    )

    volume_group = parser.add_argument_group("Volume Overrides")
    volume_group.add_argument(
        "--additional_volume_ml",
        help="Any finishing addition volume (mL) to include when computing Batch_Size_L.",
    )


def add_formulas_parser(subparsers):
    # Separate parser for gravity correction calculator
    gravity_parser = subparsers.add_parser(
        "formula-gravity", 
        help="Gravity Correction Calculator - Live updates for Corrected Gravity, ABV%, and SMV"
    )
    gravity_group = gravity_parser.add_argument_group("Measurement Inputs")
    gravity_group.add_argument(
        "--measured_temp_c", 
        help="Measured temperature for gravity correction (live updates Corrected Gravity).",
    )
    gravity_group.add_argument(
        "--measured_gravity", 
        help="Measured gravity (live updates Corrected Gravity, ABV%, SMV).",
    )
    gravity_group.add_argument(
        "--measured_brix_pct", 
        help="Measured %Brix (live updates ABV%).",
    )
    gravity_group.add_argument(
        "--calibrated_temp_c",
        choices=["20", "15.6"],
        default="20",
        widget="Dropdown",
        help="Hydrometer calibration temperature (common 20C or 15.6C).",
    )
    gravity_group.add_argument(
        "--custom_calibrated_temp",
        help="Provide a custom calibration temperature if different from the dropdown.",
    )

    # Separate parser for target profile adjustment
    target_parser = subparsers.add_parser(
        "formula-target", 
        help="Target Profile Adjustment - Pulls ferment finish values from recipe table"
    )
    target_group = target_parser.add_argument_group("Recipe Selection")
    target_group.add_argument(
        "--batch_id",
        help="BatchID to pull ferment_finish_gravity and ferment_finish_brix from recipe table.",
    )
    target_group = target_parser.add_argument_group("Current Tank State")
    target_group.add_argument(
        "--current_brix_pct",
        help="Current %Brix of the tank (or leave blank to use recipe ferment_finish_brix).",
    )
    target_group.add_argument(
        "--current_gravity",
        help="Current gravity of the tank (or leave blank to use recipe ferment_finish_gravity).",
    )
    target_group.add_argument(
        "--current_volume_l",
        required=True,
        help="Current volume in liters.",
    )
    target_group.add_argument(
        "--target_profile",
        choices=list(TARGET_PROFILES.keys()),
        default="Pure",
        widget="Dropdown",
        help="Target profile to hit.",
    )
    target_group.add_argument(
        "--amazake_ingredient_id",
        help="ingredientID for the 35Bx amazake addition (for logging in notes).",
    )


def add_database_view_parser(subparsers):
    parser = subparsers.add_parser(
        "view-database", 
        help="Preview database records in a scrollable table (ordered by BatchID, opens in new window)"
    )
    parser.add_argument(
        "--table",
        choices=["ingredients", "recipes", "starters", "publishnotes"],
        default="recipes",
        widget="Dropdown",
        help="Table to preview.",
    )
    parser.add_argument(
        "--limit",
        default="100",
        help="Number of records to display (default 100, scrollable).",
    )
    parser.add_argument(
        "--batch_id",
        help="Optional BatchID filter (for recipes/starters/publishnotes).",
    )


def add_google_sync_parser(subparsers):
    parser = subparsers.add_parser("sync-google", help="Initiate Google Sheet sync/backup")
    parser.add_argument(
        "--direction",
        choices=["from_sheet", "to_sheet"],
        default="from_sheet",
        widget="Dropdown",
        help="Pull data from Google (from_sheet) or push local data up (to_sheet).",
    )
    parser.add_argument(
        "--spreadsheet_id",
        required=True,
        help="Google Sheet spreadsheet ID (see google_sheets_sync.py).",
    )
    parser.add_argument(
        "--credentials_path",
        default="credentials.json",
        help="Path to Google credentials JSON (defaults to ./credentials.json).",
    )


def handle_add_ingredient(args, session):
    ingredient = Ingredient(
        ingredient_type=args.ingredient_type,
        acc_date=parse_date_value(args.acc_date, "Accession date", required=True),
        ingredientID=None,  # Will be set from Google Sheet sync, or can be added manually
        source=coalesce_text(args.source),
        description=coalesce_text(args.description),
    )
    session.add(ingredient)
    session.commit()
    print(f"Ingredient saved with ingredientID {ingredient.ingredientID}.")


def handle_add_recipe(args, session, cache: Dict[str, ChoiceSet]):
    batch_id = coalesce_text(args.batch_id)
    if not batch_id:
        raise ValueError("BatchID is required.")

    start_date = parse_date_value(args.start_date, "Start date", required=True)
    pouch_date = parse_date_value(args.pouch_date, "Pouch date") if args.pouch_date else None

    # Parse batch number from batchID if not provided
    batch_number = parse_int_value(args.batch_number, "Batch number")
    if batch_number is None and batch_id:
        # Try to extract number from batchID (e.g., "BATCH-001" -> 1, "2024-01" -> 1)
        import re
        numbers = re.findall(r'\d+', batch_id)
        if numbers:
            try:
                batch_number = int(numbers[-1])  # Use last number found
            except ValueError:
                pass

    kake_id = cache["kake"].resolve(args.kake, required=True, label="kake rice")
    koji_id = cache["koji"].resolve(args.koji, required=True, label="koji rice")
    yeast_id = cache["yeast"].resolve(args.yeast, required=True, label="yeast")
    water_id = cache["water"].resolve(args.water_type, required=True, label="water source")
    starter_id = cache["starter_batches"].resolve(
        args.starter_batch, required=False, label="starter batch"
    )

    if starter_id is None:
        starter_id = create_shubo_starter(
            session=session,
            batch_id=batch_id,
            start_date_value=start_date,
            kake_id=kake_id,
            koji_id=koji_id,
            yeast_id=yeast_id,
            water_id=water_id,
        )

    total_kake = parse_float_value(args.total_kake_g, "Total kake (g)")
    total_koji = parse_float_value(args.total_koji_g, "Total koji (g)")
    total_water = parse_float_value(args.total_water_ml, "Total water (mL)")
    ferment_temp = parse_float_value(args.ferment_temp_c, "Ferment temp (°C)") or 6.0
    
    # Handle style - check if creating new style
    style_value = args.style
    if style_value == "-- create new style --":
        new_style = coalesce_text(args.new_style_name)
        if not new_style:
            raise ValueError("New style name is required when creating a new style.")
        style_value = new_style
        # Note: This will be stored but won't be validated against StyleEnum
        # You may want to add it to the database or enum in the future
    ferment_finish_gravity = parse_float_value(
        args.ferment_finish_gravity, "Ferment finish gravity"
    )
    ferment_finish_brix = parse_float_value(args.ferment_finish_brix, "Ferment finish %Brix")
    final_temp = parse_float_value(args.final_measured_temp_c, "Final measured temp (°C)")
    final_gravity_input = parse_float_value(args.final_measured_gravity, "Final measured gravity")
    final_brix = parse_float_value(args.final_measured_brix_pct, "Final measured %Brix")
    calibrated_temp = parse_float_value(
        args.hydrometer_calibrated_temp, "Hydrometer calibrated temp"
    ) or 20.0
    final_water_addition = parse_float_value(
        args.final_water_addition_ml, "Final water addition (mL)"
    )

    calculated_final_gravity = None
    if final_temp is not None and final_gravity_input is not None:
        calculated_final_gravity = calculate_final_gravity(
            measured_temp_C=final_temp,
            measured_gravity=final_gravity_input,
            calibrated_temp_C=calibrated_temp,
        )

    abv_pct = calculate_abv(final_brix, calculated_final_gravity) if calculated_final_gravity else None
    smv = calculate_smv(calculated_final_gravity) if calculated_final_gravity else None

    data = {
        "batchID": batch_id,
        "start_date": start_date,
        "pouch_date": pouch_date,
        "batch": batch_number,
        "style": style_value,
        "kake": kake_id,
        "koji": koji_id,
        "yeast": yeast_id,
        "starter": starter_id,
        "water_type": water_id,
        "total_kake_g": total_kake,
        "total_koji_g": total_koji,
        "total_water_mL": total_water,
        "ferment_temp_C": ferment_temp,
        "Addition1_Notes": coalesce_text(args.addition1_notes),
        "Addition2_Notes": coalesce_text(args.addition2_notes),
        "Addition3_Notes": coalesce_text(args.addition3_notes),
        "ferment_finish_gravity": ferment_finish_gravity,
        "ferment_finish_brix": ferment_finish_brix,
        "final_measured_temp_C": final_temp,
        "final_measured_gravity": final_gravity_input,
        "final_measured_Brix_pct": final_brix,
        "final_gravity": calculated_final_gravity,
        "ABV_pct": abv_pct,
        "SMV": smv,
        "final_water_addition_mL": final_water_addition,
        "clarified": args.clarified,
        "pasteurized": args.pasteurized,
        "pasteurization_notes": coalesce_text(args.pasteurization_notes),
        "finishing_additions": coalesce_text(args.finishing_additions),
    }

    recipe = session.get(Recipe, batch_id)
    action = "updated"
    if recipe is None:
        recipe = Recipe(**data)
        action = "created"
        session.add(recipe)
    else:
        for field, value in data.items():
            setattr(recipe, field, value)

    session.commit()
    print(f"Recipe {batch_id} {action}.")


def handle_add_starter(args, session, cache: Dict[str, ChoiceSet]):
    # StarterBatch is now a string (e.g., "s64", "s100")
    starter_batch_raw = coalesce_text(args.starter_batch)
    if not starter_batch_raw:
        raise ValueError("Starter batch is required.")
    
    # Format as "s##" if it's a number, or keep as-is if already formatted
    starter_batch = format_starter_code(starter_batch_raw)
    starter_date = parse_date_value(args.starter_date, "Starter date", required=True)

    kake_id = cache["kake"].resolve(args.kake, required=True, label="kake rice")
    koji_id = cache["koji"].resolve(args.koji, required=True, label="koji rice")
    yeast_id = cache["yeast"].resolve(args.yeast, required=True, label="yeast")
    water_id = cache["water"].resolve(args.water_type, required=True, label="water source")

    data = {
        "StarterBatch": starter_batch,
        "Date": starter_date,
        "BatchID": coalesce_text(args.batch_id),
        "Amt_Kake": parse_float_value(args.amt_kake_g, "Amt_Kake (g)"),
        "Amt_Koji": parse_float_value(args.amt_koji_g, "Amt_Koji (g)"),
        "Amt_water": parse_float_value(args.amt_water_ml, "Amt_water (mL)"),
        "water_type": water_id,
        "Kake": kake_id,
        "Koji": koji_id,
        "yeast": yeast_id,
        "lactic_acid": parse_float_value(args.lactic_acid_g, "Lactic acid (g)"),
        "MgSO4": parse_float_value(args.mgso4_g, "MgSO4 (g)"),
        "KCl": parse_float_value(args.kcl_g, "KCl (g)"),
        "temp_C": parse_float_value(args.starter_temp_c, "Starter temp (°C)"),
    }

    starter = session.get(Starter, starter_batch)
    action = "updated"
    if starter is None:
        starter = Starter(**data)
        session.add(starter)
        action = "created"
    else:
        for field, value in data.items():
            setattr(starter, field, value)

    session.commit()
    print(f"Starter batch {starter_batch} {action}.")

    if starter.BatchID:
        update_recipe_totals(session, starter.BatchID)


def update_recipe_totals(session, batch_id: str):
    recipe = session.get(Recipe, batch_id)
    if recipe is None:
        print(f"No recipe found for BatchID {batch_id}; totals not updated.")
        return

    stmt = select(Starter).where(Starter.BatchID == batch_id)
    starters = session.exec(stmt).all()

    total_kake = sum_optional([s.Amt_Kake for s in starters])
    total_koji = sum_optional([s.Amt_Koji for s in starters])
    total_water = sum_optional([s.Amt_water for s in starters])

    if total_kake is not None:
        recipe.total_kake_g = total_kake
    if total_koji is not None:
        recipe.total_koji_g = total_koji
    if total_water is not None:
        recipe.total_water_mL = total_water

    session.add(recipe)
    session.commit()
    print(f"Recipe {batch_id} totals refreshed from starters.")


def handle_publish(args, session, cache: Dict[str, ChoiceSet]):
    batch_id = coalesce_text(args.batch_id)
    if not batch_id:
        raise ValueError("BatchID is required to create publish notes.")

    recipe = session.get(Recipe, batch_id)
    if recipe is None:
        raise ValueError("Recipe not found; create the recipe before publishing notes.")

    pouch_date = parse_date_value(args.pouch_date, "Pouch date") if args.pouch_date else recipe.pouch_date
    style_override = args.style_override
    
    # Normalize style - handle human-readable names
    if not style_override or style_override == STYLE_PLACEHOLDER:
        # Use recipe style, but normalize it
        style = normalize_style(recipe.style) if recipe.style else recipe.style
    else:
        # Normalize the override style (handles "Rustic Experimental" -> "rustic_experimental")
        style = normalize_style(style_override)
        if style is None:
            # If normalization failed, try using the value as-is (might be a custom style)
            style = style_override
    selected_water = cache["water"].resolve(
        args.water_choice, required=False, label="water source"
    )
    water_id = selected_water or recipe.water_type

    finishing_volume = parse_float_value(args.additional_volume_ml, "Finishing volume (mL)") or 0.0
    total_water = (recipe.total_water_mL or 0.0) + (recipe.final_water_addition_mL or 0.0) + finishing_volume
    batch_size_l = round(total_water / 1000.0, 2) if total_water else None

    rice_description = ""
    if recipe.kake:
        rice = session.get(Ingredient, recipe.kake)
        if rice:
            descriptor = rice.description or rice.source or "Ingredient"
            rice_description = f"{rice.ID} - {descriptor}"

    publish = session.get(PublishNote, batch_id)
    action = "updated"
    data = {
        "BatchID": batch_id,
        "Pouch_Date": pouch_date,
        "Style": style,
        "Water": water_id,
        "ABV": recipe.ABV_pct,
        "SMV": recipe.SMV,
        "Batch_Size_L": batch_size_l,
        "Rice": rice_description,
        "Description": coalesce_text(args.description),
    }

    if publish is None:
        publish = PublishNote(**data)
        session.add(publish)
        action = "created"
    else:
        for field, value in data.items():
            setattr(publish, field, value)

    session.commit()
    print(f"Publish note for batch {batch_id} {action}.")


def handle_formula_gravity(args, session):
    """Handle gravity correction calculator with live updates"""
    measured_temp = parse_float_value(args.measured_temp_c, "Measured temp")
    measured_gravity = parse_float_value(args.measured_gravity, "Measured gravity")
    measured_brix = parse_float_value(args.measured_brix_pct, "Measured %Brix")
    calibrated_choice = parse_float_value(args.calibrated_temp_c, "Calibrated temp") or 20.0
    custom_cal = parse_float_value(args.custom_calibrated_temp, "Custom calibration temp")
    calibrated_temp = custom_cal or calibrated_choice

    corrected_gravity = None
    if measured_temp is not None and measured_gravity is not None:
        corrected_gravity = calculate_final_gravity(
            measured_temp_C=measured_temp,
            measured_gravity=measured_gravity,
            calibrated_temp_C=calibrated_temp,
        )

    abv = calculate_abv(measured_brix, corrected_gravity) if corrected_gravity else None
    smv = calculate_smv(corrected_gravity) if corrected_gravity else None

    print("\n--- Gravity Correction Calculator (Live Updates) ---")
    if corrected_gravity is not None:
        print(f"Corrected Gravity: {corrected_gravity}")
    else:
        print("Corrected Gravity: (enter measured temp and gravity)")
    if abv is not None:
        print(f"ABV%: {abv}")
    else:
        print("ABV%: (enter measured brix and corrected gravity)")
    if smv is not None:
        print(f"SMV: {smv}")
    else:
        print("SMV: (enter corrected gravity)")


def handle_formula_target(args, session):
    """Handle target profile adjustment - pulls from recipe table if batchID provided"""
    batch_id = coalesce_text(args.batch_id)
    
    # Pull ferment finish values from recipe table if batchID provided
    current_brix = parse_float_value(args.current_brix_pct, "Current %Brix")
    current_gravity = parse_float_value(args.current_gravity, "Current gravity")
    
    if batch_id:
        recipe = session.get(Recipe, batch_id)
        if recipe:
            if current_brix is None and recipe.ferment_finish_brix is not None:
                current_brix = recipe.ferment_finish_brix
                print(f"Using ferment_finish_brix from recipe BatchID {batch_id}: {current_brix}")
            if current_gravity is None and recipe.ferment_finish_gravity is not None:
                current_gravity = recipe.ferment_finish_gravity
                print(f"Using ferment_finish_gravity from recipe BatchID {batch_id}: {current_gravity}")
        else:
            print(f"Warning: Recipe with BatchID {batch_id} not found.")
    
    current_volume = parse_float_value(args.current_volume_l, "Current volume (L)")
    target = TARGET_PROFILES[args.target_profile]
    amazake_id = parse_int_value(args.amazake_ingredient_id, "Amazake ingredientID")

    dilution = None
    if current_brix is not None and current_gravity is not None and current_volume is not None:
        dilution = calculate_dilution_adjustment(
            current_brix=current_brix,
            current_gravity=current_gravity,
            target_brix=target["brix"],
            target_gravity=target["gravity"],
            current_volume_L=current_volume,
            fortifier_brix=35.0,
        )
        if amazake_id:
            dilution["amazake_ingredient_id"] = amazake_id

    print("\n--- Target Profile Adjustment ---")
    if dilution:
        print("Dilution Guidance:")
        for key, value in dilution.items():
            print(f"  {key}: {value}")
    else:
        print("Enter current brix, gravity, and volume to calculate dilution guidance.")


def handle_view_database(args, session):
    """Display database records in a scrollable table format, ordered by BatchID"""
    table = args.table
    model = MODEL_MAP[table]
    limit = parse_int_value(args.limit, "Limit") or 100
    batch_filter = coalesce_text(args.batch_id)

    stmt = select(model)
    if batch_filter:
        if table == "recipes":
            stmt = stmt.where(Recipe.batchID == batch_filter)
        elif table == "starters":
            stmt = stmt.where(Starter.BatchID == batch_filter)
        elif table == "publishnotes":
            stmt = stmt.where(PublishNote.BatchID == batch_filter)
    
    # Order by BatchID (or appropriate ID field) for all tables
    if table == "recipes":
        stmt = stmt.order_by(Recipe.batchID)
    elif table == "starters":
        # For starters, order by BatchID first, then StarterBatch
        # Note: StarterBatch is now a string, so ordering will be alphabetical
        # For numeric ordering of "s64", "s100", we'd need custom sorting
        stmt = stmt.order_by(Starter.BatchID, Starter.StarterBatch)
    elif table == "publishnotes":
        stmt = stmt.order_by(PublishNote.BatchID)
    else:
        # For ingredients, use ID
        stmt = stmt.order_by(Ingredient.ingredientID)
    
    stmt = stmt.limit(limit)

    rows = session.exec(stmt).all()
    if not rows:
        print(f"No rows found for {table} with the given filters.")
        return

    print(f"\n{'='*80}")
    print(f"Database View: {table.upper()} (ordered by BatchID)")
    print(f"Displaying {len(rows)} record(s) - Scrollable table view")
    print(f"{'='*80}\n")
    
    # Print as a table format
    for i, row in enumerate(rows, 1):
        payload = record_to_dict(row)
        print(f"\n--- Record {i} ---")
        for key, value in payload.items():
            print(f"  {key}: {value}")
    
    print(f"\n{'='*80}")
    print(f"End of {table} records (showing {len(rows)} of up to {limit})")
    print(f"{'='*80}")


def handle_google_sync(args):
    spreadsheet_id = coalesce_text(args.spreadsheet_id)
    if not spreadsheet_id:
        raise ValueError("Spreadsheet ID is required for Google sync.")
    creds_path = args.credentials_path
    if args.direction == "from_sheet":
        sync_from_google_sheets(spreadsheet_id=spreadsheet_id, creds_path=creds_path)
        print("Imported data from Google Sheet.")
    else:
        sync_to_google_sheets(spreadsheet_id=spreadsheet_id, creds_path=creds_path)
        print("Exported local data to Google Sheet.")


def dispatch(args, session, choice_cache: Dict[str, ChoiceSet]):
    if args.command == "add-ingredient":
        handle_add_ingredient(args, session)
    elif args.command == "add-recipe":
        handle_add_recipe(args, session, choice_cache)
    elif args.command == "add-starter":
        handle_add_starter(args, session, choice_cache)
    elif args.command == "add-publish-note":
        handle_publish(args, session, choice_cache)
    elif args.command == "formula-gravity":
        handle_formula_gravity(args, session)
    elif args.command == "formula-target":
        handle_formula_target(args, session)
    elif args.command == "view-database":
        handle_view_database(args, session)
    elif args.command == "sync-google":
        handle_google_sync(args)
    else:
        raise ValueError(f"Unknown command {args.command}")


@Gooey(
    program_name="SakeMonkey Recipe Console",
    navigation="TABBED",
    default_size=(1000, 720),
    required_cols=2,
    optional_cols=2,
    clear_before_run=True,
)
def main():
    init_database()
    session = get_session()
    try:
        choice_cache = build_choice_cache(session)
        parser = build_parser(choice_cache)
        args = parser.parse_args()
        dispatch(args, session, choice_cache)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
