"""Shopify CSV export module for generating import-ready files."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, List


SHOPIFY_HEADERS = [
    "Handle", "Title", "Body (HTML)", "Vendor", "Product Category", "Type", "Tags",
    "Published", "Option1 Name", "Option1 Value", "Option2 Name", "Option2 Value",
    "Option3 Name", "Option3 Value", "Variant SKU", "Variant Grams",
    "Variant Inventory Tracker", "Variant Inventory Qty", "Variant Inventory Policy",
    "Variant Fulfillment Service", "Variant Price", "Variant Compare At Price",
    "Variant Requires Shipping", "Variant Taxable", "Variant Barcode", "Image Src",
    "Image Position", "Image Alt Text", "Gift Card", "SEO Title", "SEO Description",
    "Google Shopping / Google Product Category", "Google Shopping / Gender",
    "Google Shopping / Age Group", "Google Shopping / MPN", "Google Shopping / Condition",
    "Google Shopping / Custom Product", "Variant Image", "Variant Weight Unit",
    "Variant Tax Code", "Cost per item", "Included / United States",
    "Price / United States", "Compare At Price / United States",
    "Included / International", "Price / International",
    "Compare At Price / International", "Status",
]

SHOPIFY_DEFAULTS = {
    "Vendor": "M&E Interior",
    "Product Category": "Uncategory",
    "Published": "FALSE",
    "Variant Grams": "0",
    "Variant Inventory Policy": "deny",
    "Variant Fulfillment Service": "manual",
    "Variant Price": "0",
    "Variant Requires Shipping": "FALSE",
    "Variant Taxable": "TRUE",
    "Gift Card": "FALSE",
    "Variant Weight Unit": "kg",
    "Status": "draft",
}


def create_handle(title: str) -> str:
    """
    Convert product title to Shopify handle format.

    Args:
        title: Product title

    Returns:
        Shopify handle (lowercase, hyphens, no special chars)
    """
    handle = title.lower()
    handle = re.sub(r"[^\w\s-]", "", handle)
    handle = re.sub(r"[-\s]+", "-", handle)
    handle = handle.strip("-")
    return handle


def detect_product_type(title: str, description: str) -> str:
    """
    Detect product type from title and description.

    Args:
        title: Product title
        description: Product description

    Returns:
        Product type string
    """
    text = (title + " " + description).lower()

    type_keywords = {
        "dining chair": ["dining chair", "side chair"],
        "lounge chair": ["lounge chair", "armchair", "accent chair"],
        "bar stool": ["bar stool", "barstool", "counter stool"],
        "dining table": ["dining table", "table"],
        "coffee table": ["coffee table", "cocktail table"],
        "side table": ["side table", "end table", "accent table"],
        "sofa": ["sofa", "couch", "sectional"],
        "bench": ["bench", "seating bench"],
        "stool": ["stool"],
        "chair": ["chair"],
    }

    for product_type, keywords in type_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return product_type

    return "furniture"


def format_description_as_html(description: str, dimensions: str = "", features: List[str] | None = None) -> str:
    """
    Format product description as HTML.

    Args:
        description: Product description text
        dimensions: Product dimensions string
        features: List of feature strings

    Returns:
        HTML-formatted description
    """
    if features is None:
        features = []

    html_parts = []

    if description:
        html_parts.append(f"<p>{description}</p>")

    if dimensions:
        html_parts.append(f"<p><strong>Dimensions:</strong> {dimensions}</p>")

    if features:
        html_parts.append("<p><strong>Features:</strong></p>")
        html_parts.append("<ul>")
        for feature in features:
            feature_clean = str(feature).strip("- •").strip()
            if feature_clean:
                html_parts.append(f"<li>{feature_clean}</li>")
        html_parts.append("</ul>")

    return "\n".join(html_parts)


def create_main_product_row(product: Dict[str, Any]) -> Dict[str, str]:
    """
    Create the main Shopify product row from product data.

    Args:
        product: Normalized product dict

    Returns:
        Shopify CSV row dict
    """
    handle = create_handle(product["title"])
    product_type = detect_product_type(product["title"], product.get("description", ""))
    body_html = format_description_as_html(
        product.get("description", ""),
        product.get("dimensions", ""),
        product.get("features", []),
    )

    row = {header: "" for header in SHOPIFY_HEADERS}
    row.update(SHOPIFY_DEFAULTS)
    row.update({
        "Handle": handle,
        "Title": product["title"],
        "Body (HTML)": body_html,
        "Type": product_type,
        "Tags": product_type,
        "Variant SKU": product.get("sku", ""),
        "Variant Price": product.get("price", "0"),
        "Variant Grams": str(product.get("grams", 0)),
        "Variant Weight Unit": product.get("weight_unit", "kg"),
        "Variant Barcode": product.get("barcode", ""),
        "SEO Title": product["title"],
        "SEO Description": product.get("description", "")[:160],
    })

    if product.get("images"):
        row["Image Src"] = product["images"][0]
        row["Image Position"] = "1"
        row["Image Alt Text"] = product.get("image_alt_text", product["title"])
    elif product.get("image_src"):
        row["Image Src"] = product["image_src"]
        row["Image Position"] = "1"
        row["Image Alt Text"] = product.get("image_alt_text", product["title"])

    return row


def create_image_rows(product: Dict[str, Any], handle: str) -> List[Dict[str, str]]:
    """
    Create additional rows for extra product images.

    Args:
        product: Product dict
        handle: Product handle

    Returns:
        List of image row dicts
    """
    image_rows = []

    images = product.get("images", [])
    if images and len(images) > 1:
        for i, image_url in enumerate(images[1:], start=2):
            row = {header: "" for header in SHOPIFY_HEADERS}
            row.update({
                "Handle": handle,
                "Image Src": image_url,
                "Image Position": str(i),
                "Image Alt Text": product.get("image_alt_text", product["title"]),
            })
            image_rows.append(row)

    return image_rows


def generate_csv_data(products: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Generate complete Shopify CSV data from product list.

    Args:
        products: List of normalized product dicts

    Returns:
        List of Shopify CSV row dicts
    """
    csv_rows = []

    for product in products:
        if not product.get("title"):
            continue

        main_row = create_main_product_row(product)
        csv_rows.append(main_row)

        handle = main_row["Handle"]
        image_rows = create_image_rows(product, handle)
        csv_rows.extend(image_rows)

    return csv_rows


def export_to_csv(products: List[Dict[str, Any]], filepath: str) -> Dict[str, Any]:
    """
    Export product data to Shopify CSV file.

    Args:
        products: List of normalized product dicts
        filepath: Output CSV file path

    Returns:
        Dict with:
            - success (bool)
            - filepath (str): Path to generated file
            - product_count (int): Number of products
            - row_count (int): Total CSV rows
            - error (str): Error message if failed
    """
    try:
        csv_data = generate_csv_data(products)

        if not csv_data:
            return {
                "success": False,
                "filepath": "",
                "product_count": 0,
                "row_count": 0,
                "error": "No valid products to export",
            }

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=SHOPIFY_HEADERS)
            writer.writeheader()
            writer.writerows(csv_data)

        main_products = len([r for r in csv_data if r["Image Position"] == "1" or r["Image Position"] == ""])
        image_rows = len(csv_data) - main_products

        return {
            "success": True,
            "filepath": str(path.absolute()),
            "product_count": main_products,
            "row_count": len(csv_data),
            "image_row_count": image_rows,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "filepath": "",
            "product_count": 0,
            "row_count": 0,
            "error": f"CSV export failed: {str(e)}",
        }
