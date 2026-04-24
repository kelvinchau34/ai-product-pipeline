"""Data ingestion module for loading product data from various sources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


def load_csv(filepath: str) -> Dict[str, Any]:
    """
    Load product data from CSV file.

    Args:
        filepath: Path to CSV file

    Returns:
        Dict with keys:
            - success (bool)
            - records (list): List of product dicts
            - count (int): Number of records loaded
            - error (str): Error message if failed
    """
    try:
        path = Path(filepath)
        if not path.exists():
            return {
                "success": False,
                "records": [],
                "count": 0,
                "error": f"File not found: {filepath}",
            }

        df = pd.read_csv(filepath)
        records = df.to_dict("records")

        return {
            "success": True,
            "records": records,
            "count": len(records),
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "records": [],
            "count": 0,
            "error": f"Failed to load CSV: {str(e)}",
        }


def load_json(filepath: str) -> Dict[str, Any]:
    """
    Load product data from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        Dict with keys:
            - success (bool)
            - records (list): List of product dicts
            - count (int): Number of records loaded
            - error (str): Error message if failed
    """
    try:
        path = Path(filepath)
        if not path.exists():
            return {
                "success": False,
                "records": [],
                "count": 0,
                "error": f"File not found: {filepath}",
            }

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both list and nested structures
        records = data if isinstance(data, list) else [data]

        return {
            "success": True,
            "records": records,
            "count": len(records),
            "error": None,
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "records": [],
            "count": 0,
            "error": f"Invalid JSON: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "records": [],
            "count": 0,
            "error": f"Failed to load JSON: {str(e)}",
        }


def load_data(filepath: str) -> Dict[str, Any]:
    """
    Auto-detect file format and load product data.

    Args:
        filepath: Path to CSV or JSON file

    Returns:
        Dict with ingestion results
    """
    path = Path(filepath)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return load_csv(filepath)
    elif suffix == ".json":
        return load_json(filepath)
    else:
        return {
            "success": False,
            "records": [],
            "count": 0,
            "error": f"Unsupported file format: {suffix}",
        }
