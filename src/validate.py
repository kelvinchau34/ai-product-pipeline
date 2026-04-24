"""Data validation module for checking product data integrity."""

from __future__ import annotations

from typing import Any, Dict, List


REQUIRED_FIELDS = ["title", "sku"]


def validate_product(record: Dict[str, Any]) -> List[str]:
    """
    Validate a single product record.

    Args:
        record: Product dict to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors: List[str] = []

    for field in REQUIRED_FIELDS:
        if not record.get(field):
            errors.append(f"missing_required_field:{field}")

    # Additional validation checks
    if record.get("price"):
        try:
            float(record["price"])
        except (ValueError, TypeError):
            errors.append(f"invalid_price:{record['price']}")

    if record.get("grams"):
        try:
            int(record["grams"])
        except (ValueError, TypeError):
            errors.append(f"invalid_grams:{record['grams']}")

    return errors


def validate_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a list of product records.

    Args:
        records: List of product dicts to validate

    Returns:
        Dict with:
            - success (bool): All records valid
            - valid_records (list): List of valid product dicts
            - invalid_records (list): List of dicts with index and errors
            - valid_count (int): Number of valid records
            - invalid_count (int): Number of invalid records
            - error (str): Overall error message if failed
    """
    try:
        valid_records: List[Dict[str, Any]] = []
        invalid_records: List[Dict[str, Any]] = []

        for idx, record in enumerate(records):
            errors = validate_product(record)
            if errors:
                invalid_records.append({
                    "index": idx,
                    "record": record,
                    "errors": errors,
                })
            else:
                valid_records.append(record)

        return {
            "success": len(invalid_records) == 0,
            "valid_records": valid_records,
            "invalid_records": invalid_records,
            "valid_count": len(valid_records),
            "invalid_count": len(invalid_records),
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "valid_records": [],
            "invalid_records": [],
            "valid_count": 0,
            "invalid_count": len(records),
            "error": f"Validation failed: {str(e)}",
        }
