"""Data normalization module for standardizing product fields."""

from __future__ import annotations

import math
from typing import Any, Dict, List

import pandas as pd


def clean_value(val: Any, default: Any = None) -> Any:
    """
    Clean and standardize field values, handling NaN and missing data.

    Args:
        val: Value to clean
        default: Default value if val is missing

    Returns:
        Cleaned value or default
    """
    if val is None:
        return default
    if isinstance(val, float) and math.isnan(val):
        return default
    if pd.isna(val):
        return default
    return val


def normalize_product(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a single product record to standard fields.

    Args:
        record: Raw product record

    Returns:
        Normalized product dict with standard keys
    """
    return {
        "handle": clean_value(record.get("handle"), ""),
        "title": str(clean_value(record.get("title"), "")).strip(),
        "description": str(clean_value(record.get("description"), "")).strip(),
        "body_html": str(clean_value(record.get("body_html"), record.get("Body (HTML)"), "")).strip(),
        "vendor": str(clean_value(record.get("vendor"), "Default Vendor")).strip(),
        "product_type": str(clean_value(record.get("type", "type"), "General")).strip(),
        "tags": str(clean_value(record.get("tags"), "")).strip(),
        "status": str(clean_value(record.get("status"), "draft")).strip(),
        "dimensions": str(clean_value(record.get("dimensions"), "")).strip(),
        "features": clean_value(record.get("features"), []),
        "sku": str(clean_value(record.get("sku", "variant_sku"), "")).strip(),
        "price": str(clean_value(record.get("price", "variant_price"), "0.00")).strip(),
        "grams": int(clean_value(record.get("grams", "variant_grams"), 0)),
        "weight_unit": str(clean_value(record.get("weight_unit", "variant_weight_unit"), "kg")).strip(),
        "barcode": str(clean_value(record.get("barcode", "variant_barcode"), "")).strip(),
        "images": clean_value(record.get("images"), []),
        "image_src": str(clean_value(record.get("image_src", "image_src"), "")).strip(),
        "image_alt_text": str(clean_value(record.get("image_alt_text", "image_alt_text"), "")).strip(),
    }


def normalize_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Normalize a list of product records.

    Args:
        records: List of raw product dicts

    Returns:
        Dict with:
            - success (bool)
            - records (list): Normalized records
            - count (int): Number of normalized records
            - error (str): Error message if failed
    """
    try:
        normalized = [normalize_product(rec) for rec in records]

        return {
            "success": True,
            "records": normalized,
            "count": len(normalized),
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "records": [],
            "count": 0,
            "error": f"Normalization failed: {str(e)}",
        }
