"""Data ingestion module for loading product data from various sources."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict


def load_csv(filepath: str) -> Dict[str, Any]:
    try:
        path = Path(filepath)
        if not path.exists():
            return {"success": False, "records": [], "count": 0, "error": f"File not found: {filepath}"}

        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            records = [dict(row) for row in reader]

        return {"success": True, "records": records, "count": len(records), "error": None}
    except Exception as e:
        return {"success": False, "records": [], "count": 0, "error": f"Failed to load CSV: {str(e)}"}


def load_json(filepath: str) -> Dict[str, Any]:
    try:
        path = Path(filepath)
        if not path.exists():
            return {"success": False, "records": [], "count": 0, "error": f"File not found: {filepath}"}

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = data if isinstance(data, list) else [data]
        return {"success": True, "records": records, "count": len(records), "error": None}
    except json.JSONDecodeError as e:
        return {"success": False, "records": [], "count": 0, "error": f"Invalid JSON: {str(e)}"}
    except Exception as e:
        return {"success": False, "records": [], "count": 0, "error": f"Failed to load JSON: {str(e)}"}


def load_data(filepath: str) -> Dict[str, Any]:
    suffix = Path(filepath).suffix.lower()
    if suffix == ".csv":
        return load_csv(filepath)
    elif suffix == ".json":
        return load_json(filepath)
    return {"success": False, "records": [], "count": 0, "error": f"Unsupported file format: {suffix}"}
