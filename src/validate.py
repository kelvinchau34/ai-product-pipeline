"""Data validation module for checking product data integrity."""

from __future__ import annotations

from typing import Any, Dict, List

from src.exporter import create_handle


REQUIRED_FIELDS = ["title", "sku"]
MIN_DESCRIPTION_LENGTH = 40


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


def build_handle_counts(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """Build counts of Shopify handles for duplicate detection."""
    counts: Dict[str, int] = {}
    for record in records:
        handle = create_handle(str(record.get("title", "")))
        if handle:
            counts[handle] = counts.get(handle, 0) + 1
    return counts


def _build_issue(code: str, severity: str, field: str, message: str) -> Dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "field": field,
        "message": message,
    }


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def generate_issues(record: Dict[str, Any], handle_counts: Dict[str, int] | None = None) -> List[Dict[str, str]]:
    """Generate deterministic issues for a normalized product record."""
    issues: List[Dict[str, str]] = []

    errors = validate_product(record)
    for error in errors:
        if error.startswith("missing_required_field:"):
            field = error.split(":", 1)[1]
            code = f"missing_{field}"
            issues.append(_build_issue(code, "error", field, f"Missing required field: {field}"))
        elif error.startswith("invalid_price:"):
            issues.append(_build_issue("invalid_price", "error", "price", "Price must be a number"))
        elif error.startswith("invalid_grams:"):
            issues.append(_build_issue("invalid_grams", "error", "grams", "Weight must be an integer"))

    title = str(record.get("title", ""))
    description = str(record.get("description_long") or record.get("description") or "").strip()
    images = record.get("images") or []
    image_src = str(record.get("image_src") or "").strip()

    if _is_blank(record.get("price")):
        issues.append(_build_issue("missing_price", "warning", "price", "Price is missing"))

    if _is_blank(record.get("vendor")):
        issues.append(_build_issue("missing_vendor", "warning", "vendor", "Vendor is missing"))

    if _is_blank(images) and _is_blank(image_src):
        issues.append(_build_issue("missing_images", "warning", "images", "No product images found"))

    if (
        _is_blank(record.get("height_mm"))
        and _is_blank(record.get("width_mm"))
        and _is_blank(record.get("depth_mm"))
        and _is_blank(record.get("dimensions"))
    ):
        issues.append(_build_issue("missing_dimensions", "warning", "dimensions", "Dimensions are missing"))

    if _is_blank(record.get("features")):
        issues.append(_build_issue("missing_materials", "warning", "features", "Materials are missing"))

    if description and len(description) < MIN_DESCRIPTION_LENGTH:
        issues.append(
            _build_issue("description_too_short", "warning", "description", "Description is too short")
        )

    for image_url in images:
        image_url = str(image_url).strip()
        if image_url and not image_url.lower().startswith(("http://", "https://")):
            issues.append(_build_issue("invalid_image_url", "warning", "images", "Invalid image URL"))
            break

    if handle_counts:
        handle = create_handle(title)
        if handle and handle_counts.get(handle, 0) > 1:
            issues.append(
                _build_issue("duplicate_handle", "warning", "handle", "Duplicate handle detected")
            )

    return issues


def assign_status(issues: List[Dict[str, str]]) -> str:
    """Assign product status based on issue severity."""
    if any(issue.get("severity") == "error" for issue in issues):
        return "missing_fields"
    if issues:
        return "needs_review"
    return "ready"


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
