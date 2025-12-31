"""
Utility to correct database fields one-by-one or in bulk via Excel.

The tool wraps a small CLI with a Gooey front-end so you can run it
graphically or headless (`python db_correct.py --ignore-gooey ...`).
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from datetime import date
from typing import Any, Dict, List, Optional, Tuple, get_args, get_origin

from sqlmodel import Session

from database import get_session, init_database
from models import Ingredient, PublishNote, Recipe, Starter
from google_sheets_sync import (
    convert_ingredient_id_to_string,
    convert_style_to_database,
    parse_bool,
    parse_date,
    parse_float,
    parse_int,
    update_publish_note_batch_size,
    validate_publish_note,
    validate_recipe,
    validate_starter,
    validate_style,
)

try:
    from gooey import Gooey, GooeyParser
except Exception:  # Gooey may not be installed in some environments
    Gooey = None
    GooeyParser = argparse.ArgumentParser  # type: ignore


TABLES = {
    "ingredients": {"model": Ingredient, "pk": "ingredientID", "sheet": "Ingredients"},
    "recipe": {"model": Recipe, "pk": "batchID", "sheet": "Recipe"},
    "starters": {"model": Starter, "pk": "StarterBatch", "sheet": "Starters"},
    "publishnotes": {"model": PublishNote, "pk": "BatchID", "sheet": "PublishNotes"},
}

# Common column aliases from the Google Sheet / Excel headers
COLUMN_ALIASES = {
    "recipe": {
        "abv_%": "ABV_pct",
        "abv": "ABV_pct",
        "smv": "SMV",
        "final_measured_brix_%": "final_measured_Brix_pct",
        "final_measured_brix_pct": "final_measured_Brix_pct",
        "pasteruization_notes": "pasteurization_notes",
    },
    "starters": {
        "lactic_acid_g": "lactic_acid",
        "mgso4_g": "MgSO4",
        "kcl_g": "KCl",
    },
}

STYLE_FIELDS = {"style", "Style"}
INGREDIENT_FIELDS = {
    "kake",
    "koji",
    "yeast",
    "water_type",
    "Kake",
    "Koji",
    "Water",
}
STARTER_FIELDS = {"starter", "StarterBatch"}


def unwrap_type(tp: Any) -> Any:
    origin = get_origin(tp)
    if origin is None:
        return tp
    args = [a for a in get_args(tp) if a is not type(None)]  # noqa: E721
    return args[0] if args else tp


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def normalize_starter_batch(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if not text.lower().startswith("s"):
        try:
            num = int(float(text))
            return f"s{num}"
        except Exception:
            return f"s{text}"
    return text.lower()


def coerce_scalar(field_type: Any, raw: Any) -> Any:
    target = unwrap_type(field_type)
    if target is date:
        return parse_date(raw)
    if target is float:
        return parse_float(raw)
    if target is int:
        return parse_int(raw)
    if target is bool:
        if is_blank(raw):
            return None
        return parse_bool(raw)
    return raw


def normalize_value(table: str, field: str, value: Any, session: Session) -> Any:
    if field in STYLE_FIELDS:
        return convert_style_to_database(value) or value
    if field in INGREDIENT_FIELDS:
        return convert_ingredient_id_to_string(session, value)
    if field in STARTER_FIELDS:
        return normalize_starter_batch(value)
    return value


def build_field_map(table: str) -> Dict[str, str]:
    model_cls = TABLES[table]["model"]
    fields = {name.lower(): name for name in model_cls.__fields__.keys()}
    for alias, target in COLUMN_ALIASES.get(table, {}).items():
        fields[alias.lower()] = target
    return fields


def prepare_value(
    table: str,
    field: str,
    raw: Any,
    session: Session,
    allow_clear: bool,
    model_cls: Any,
) -> Tuple[bool, Any]:
    if is_blank(raw):
        return (allow_clear, None if allow_clear else None)
    parsed = coerce_scalar(model_cls.__fields__[field].outer_type_, raw)
    normalized = normalize_value(table, field, parsed, session)
    return True, normalized


def validate_record(session: Session, table: str, record: Any) -> List[str]:
    if table == "recipe":
        return validate_recipe(session, record)
    if table == "starters":
        return validate_starter(session, record)
    if table == "publishnotes":
        return validate_publish_note(session, record)
    if table == "ingredients":
        # ingredient rules are minimal; keep placeholder for parity
        return []
    return []


def handle_edit(args: argparse.Namespace) -> int:
    table = args.table.lower()
    config = TABLES[table]
    model_cls = config["model"]
    pk_field = config["pk"]
    if args.field not in model_cls.__fields__:
        print(f"Field '{args.field}' is not valid for table '{table}'.")
        print(f"Valid fields: {', '.join(model_cls.__fields__.keys())}")
        return 1

    init_database()
    with get_session() as session:
        record = session.get(model_cls, args.record_id)
        if not record:
            print(f"No record found with {pk_field}='{args.record_id}'.")
            return 1

        should_update, new_value = prepare_value(
            table,
            args.field,
            args.value,
            session,
            args.allow_clear,
            model_cls,
        )
        if not should_update:
            print("Value is blank and --allow-clear not set; nothing to do.")
            return 0

        candidate_data = record.dict()
        old_value = candidate_data.get(args.field)
        candidate_data[args.field] = new_value
        candidate = model_cls(**candidate_data)
        errors = validate_record(session, table, candidate)
        if errors and not args.force:
            print("Validation failed; changes not applied:")
            for err in errors:
                print(f" - {err}")
            return 1

        print(f"{table}:{pk_field}={args.record_id} -> {args.field}: {old_value} -> {new_value}")
        if args.dry_run:
            print("Dry run only; no database changes saved.")
            return 0

        for key, value in candidate_data.items():
            setattr(record, key, value)
        if table == "recipe":
            update_publish_note_batch_size(session, record)
        session.commit()
        print("Update saved.")
        return 0


def map_row_to_updates(table: str, row: Dict[str, Any]) -> Dict[str, Any]:
    field_map = build_field_map(table)
    updates: Dict[str, Any] = {}
    for raw_key, value in row.items():
        if raw_key is None:
            continue
        key_normalized = str(raw_key).strip().lower()
        if key_normalized in field_map:
            updates[field_map[key_normalized]] = value
    return updates


def handle_bulk(args: argparse.Namespace) -> int:
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        print(f"pandas is required for Excel corrections: {exc}")
        return 1

    if not os.path.exists(args.excel_path):
        print(f"Excel file not found: {args.excel_path}")
        return 1

    init_database()
    summary = {"processed": 0, "updated": 0, "skipped": 0, "errors": 0}
    sheet_filter = args.sheet.lower() if args.sheet else None

    with get_session() as session:
        xls = pd.ExcelFile(args.excel_path)
        sheet_names = xls.sheet_names
        for sheet in sheet_names:
            table = None
            sheet_lower = sheet.lower()
            for name, cfg in TABLES.items():
                if cfg["sheet"].lower() == sheet_lower or name == sheet_lower:
                    table = name
                    break
            if not table:
                continue
            if sheet_filter and sheet_lower != sheet_filter:
                continue

            df = pd.read_excel(xls, sheet_name=sheet)
            rows = df.to_dict(orient="records")
            model_cls = TABLES[table]["model"]
            pk_field = TABLES[table]["pk"]

            for row in rows:
                summary["processed"] += 1
                updates = map_row_to_updates(table, row)
                pk_value = updates.get(pk_field) or row.get(pk_field)
                if pk_value is None or is_blank(pk_value):
                    summary["errors"] += 1
                    continue

                record = session.get(model_cls, pk_value)
                if not record and not args.create_missing:
                    summary["errors"] += 1
                    continue

                base_data = record.dict() if record else {}
                base_data[pk_field] = pk_value
                for field, raw_val in updates.items():
                    should_update, parsed_val = prepare_value(
                        table,
                        field,
                        raw_val,
                        session,
                        args.allow_clear,
                        model_cls,
                    )
                    if not should_update:
                        continue
                    base_data[field] = parsed_val

                candidate = model_cls(**base_data)
                errors = validate_record(session, table, candidate)
                if errors and not args.force:
                    summary["errors"] += 1
                    continue

                if args.dry_run:
                    summary["updated"] += 1
                    continue

                if record:
                    for key, value in base_data.items():
                        setattr(record, key, value)
                    if table == "recipe":
                        update_publish_note_batch_size(session, record)
                else:
                    session.add(candidate)
                    if table == "recipe":
                        update_publish_note_batch_size(session, candidate)
                summary["updated"] += 1

            session.commit()

    print(
        "Bulk corrections complete - "
        f"processed: {summary['processed']}, "
        f"updated: {summary['updated']}, "
        f"errors: {summary['errors']}, "
        f"skipped: {summary['skipped']}"
    )
    if args.dry_run:
        print("Dry run mode; no database changes were saved.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ParserCls = GooeyParser if Gooey else argparse.ArgumentParser
    parser = ParserCls(
        description="Fix individual fields or apply Excel-based corrections to the SakeMonkey database.",
        prog="db_correct",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    edit_cmd = subparsers.add_parser("edit", help="Update a single field on one record")
    edit_cmd.add_argument("table", choices=list(TABLES.keys()), help="Target table")
    edit_cmd.add_argument(
        "record_id",
        help="Primary key value (ingredientID, batchID, StarterBatch, or BatchID for publishnotes)",
    )
    edit_cmd.add_argument("field", help="Field/column to update")
    edit_cmd.add_argument("value", help="New value (blank + --allow-clear will null the field)")
    edit_cmd.add_argument("--allow-clear", action="store_true", help="Allow blank to clear a value")
    edit_cmd.add_argument("--force", action="store_true", help="Save even if validation reports issues")
    edit_cmd.add_argument("--dry-run", action="store_true", help="Preview without writing changes")

    bulk_cmd = subparsers.add_parser("bulk", help="Apply corrections from an Excel workbook")
    bulk_cmd.add_argument(
        "excel_path",
        help="Path to Excel workbook with sheets Ingredients, Recipe, Starters, PublishNotes",
        widget="FileChooser" if Gooey else None,  # type: ignore
    )
    bulk_cmd.add_argument("--sheet", help="Process a single sheet name (optional)")
    bulk_cmd.add_argument("--allow-clear", action="store_true", help="Allow blanks to clear values")
    bulk_cmd.add_argument("--create-missing", action="store_true", help="Create rows that do not exist yet")
    bulk_cmd.add_argument("--force", action="store_true", help="Save even if validation reports issues")
    bulk_cmd.add_argument("--dry-run", action="store_true", help="Preview without writing changes")

    return parser


def run_cli() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "edit":
        return handle_edit(args)
    if args.command == "bulk":
        return handle_bulk(args)
    print("Unknown command.")
    return 1


if Gooey:

    @Gooey(
        program_name="SakeMonkey DB Corrector",
        default_size=(800, 720),
        optional_cols=1,
        navigation="SIDEBAR",
    )
    def main():
        sys.exit(run_cli())


else:

    def main():
        sys.exit(run_cli())


if __name__ == "__main__":
    main()
