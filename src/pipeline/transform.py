from __future__ import annotations

from typing import Any, Dict, List


REQUIRED_FIELDS = ["title", "sku"]


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {
        "title": str(record.get("title", "")).strip(),
        "sku": str(record.get("sku", "")).strip(),
        "description": str(record.get("description", "")).strip(),
        "price": record.get("price", "0"),
    }
    return normalized


def validate_record(record: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for field in REQUIRED_FIELDS:
        if not record.get(field):
            errors.append(f"missing_required_field:{field}")
    return errors


def process_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    processed: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    for idx, raw in enumerate(records):
        rec = normalize_record(raw)
        errs = validate_record(rec)
        if errs:
            warnings.append({"index": idx, "errors": errs})
            continue
        processed.append(rec)

    return {
        "processed_count": len(processed),
        "warning_count": len(warnings),
        "records": processed,
        "warnings": warnings,
    }
