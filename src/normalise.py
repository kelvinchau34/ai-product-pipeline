"""Data normalization module for standardizing product fields."""

from __future__ import annotations

import math
import re
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


def parse_weight(weight_str: str | None) -> int:
    """
    Parse weight string (handles European decimal format like "3,00") to grams (int).

    Args:
        weight_str: Weight value as string (e.g., "3,00", "3.50")

    Returns:
        Weight in grams as integer
    """
    if not weight_str:
        return 0
    try:
        # Replace European decimal comma with standard period
        weight_str = str(weight_str).strip().replace(",", ".")
        # Extract numeric value (handles units like "kg")
        match = re.search(r"[\d.]+", weight_str)
        if match:
            weight_float = float(match.group())
            # Assume input is in kg, convert to grams
            return int(weight_float * 1000)
        return 0
    except (ValueError, TypeError):
        return 0


def extract_images(record: Dict[str, Any]) -> List[str]:
    """
    Extract image URLs from record, prioritizing Packshot then Lifestyle images.

    Args:
        record: Product record

    Returns:
        List of image URLs (non-empty)
    """
    images = []
    # Add Packshot images (1-5)
    for i in range(1, 6):
        img_url = clean_value(record.get(f"Packshot {i}"), "")
        if img_url and str(img_url).strip() and str(img_url).lower() != "na":
            images.append(str(img_url).strip())

    # Add Lifestyle images (1-5)
    for i in range(1, 6):
        img_url = clean_value(record.get(f"Lifestyle {i}"), "")
        if img_url and str(img_url).strip() and str(img_url).lower() != "na":
            images.append(str(img_url).strip())

    return images


def extract_materials(materials_str: str | None) -> List[str]:
    """
    Extract materials list from comma-separated string.

    Args:
        materials_str: Materials as comma-separated string

    Returns:
        List of materials
    """
    if not materials_str:
        return []
    return [m.strip() for m in str(materials_str).split(",") if m.strip()]


def build_description(record: Dict[str, Any]) -> str:
    """
    Build enriched description combining Product Text, Description, Designer info.

    Args:
        record: Product record

    Returns:
        Enriched description string (HTML)
    """
    parts = []

    # Add Product Text (primary description)
    product_text = clean_value(record.get("Product Text"), "").strip()
    if product_text:
        parts.append(product_text)

    # Add Designer info
    designer = clean_value(record.get("Designer"), "").strip()
    designer_bio = clean_value(record.get("Designer Bio"), "").strip()
    if designer or designer_bio:
        designer_section = f"<p><strong>Designer:</strong> {designer}"
        if designer_bio:
            designer_section += f"<br>{designer_bio}"
        designer_section += "</p>"
        parts.append(designer_section)

    # Add Material info
    materials = clean_value(record.get("Materials"), "").strip()
    if materials:
        parts.append(f"<p><strong>Materials:</strong> {materials}</p>")

    # Add dimensions
    dims = []
    for dim_key in ["Length mm", "Width mm", "Height mm", "Dia. mm."]:
        val = str(clean_value(record.get(dim_key), "")).strip()
        if val:
            dims.append(f"{dim_key}: {val}")
    if dims:
        parts.append(f"<p><strong>Dimensions:</strong> {', '.join(dims)}</p>")

    return "\n".join(parts)


def normalize_product(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a single product record to standard fields.
    Handles both generic Shopify fields and supplier-specific WOUD columns.

    Args:
        record: Raw product record

    Returns:
        Normalized product dict with standard keys
    """
    # Extract key fields
    description_text = clean_value(record.get("Description"), "") or clean_value(
        record.get("Description 2"), ""
    )
    title = str(description_text).strip() or "Unnamed Product"

    # Extract price (default to German EUR price)
    price_raw = clean_value(record.get("DE RRP incl. VAT (EUR)"), "0.00")
    price_str = str(price_raw).replace(",", ".").strip()

    # Extract and normalize weight
    weight_raw = clean_value(record.get("Weight"), "0")
    grams = parse_weight(str(weight_raw))

    # Extract category (maps to Shopify product_type)
    category = clean_value(record.get("Category"), "General").strip()

    # Extract colour and materials as tags/features
    colour = clean_value(record.get("Colour"), "").strip()
    materials = extract_materials(clean_value(record.get("Materials"), ""))

    # Build tags (colour + category)
    tags_list = [category]
    if colour:
        tags_list.append(colour)
    tags_str = ", ".join(tags_list)

    # Combine features (materials)
    features = materials if materials else []

    product_text = str(clean_value(record.get("Product Text"), "")).strip()
    description_2 = str(clean_value(record.get("Description 2"), "")).strip()

    return {
        "handle": str(clean_value(record.get("Item no."), "")).strip().lower(),
        "title": title,
        "description": description_text,
        "description_long": product_text or description_text,
        "designs_available": description_2,
        "fabric_colour": colour,
        "body_html": build_description(record),
        "vendor": "WOUD",
        "product_type": category,
        "tags": tags_str,
        "status": "active" if clean_value(record.get("Item status"), "").upper() == "ACTIVE" else "draft",
        "dimensions": ", ".join(
            [
                f"{k}: {clean_value(record.get(k), '')}mm"
                for k in ["Length mm", "Width mm", "Height mm"]
                if clean_value(record.get(k), "")
            ]
        ),
        "features": features,
        "sku": str(clean_value(record.get("Item no."), "")).strip(),
        "price": price_str,
        "grams": grams,
        "weight_unit": "g",
        "weight_display": str(clean_value(record.get("Weight"), "")).strip(),
        "barcode": str(clean_value(record.get("EAN"), "")).strip(),
        "height_mm": clean_value(record.get("Height mm"), ""),
        "width_mm": clean_value(record.get("Width mm"), ""),
        "depth_mm": clean_value(record.get("Length mm"), ""),
        "certifications": str(clean_value(record.get("Certifications"), "")).strip(),
        "care_guide_url": str(clean_value(record.get("Care guide"), "")).strip(),
        "assembly_instruction_url": str(clean_value(record.get("Assembly instruction"), "")).strip(),
        "images": extract_images(record),
        "image_src": "",
        "image_alt_text": title,
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
