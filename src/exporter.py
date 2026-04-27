"""Shopify CSV export module for generating import-ready files."""

from __future__ import annotations

import csv
import html
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


def _escape_text(value: Any) -> str:
    return html.escape(str(value or "").strip())


def _html_paragraph_text(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    lines = [html.escape(line.strip()) for line in text.replace("\r", "").split("\n") if line.strip()]
    return "<br><br>".join(lines)


def _parse_float(value: Any) -> float | None:
    raw = str(value or "").strip().replace(",", ".")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _format_mm_to_cm(value: Any) -> str:
    mm = _parse_float(value)
    if mm is None:
        return ""
    cm = mm / 10.0
    if cm.is_integer():
        return f"{int(cm)}cm"
    return f"{cm:.1f}cm"


def _format_weight_kg(value: Any) -> str:
    kg = _parse_float(value)
    if kg is None:
        return ""
    if kg.is_integer():
        return f"{int(kg)}kg"
    return f"{kg:.2f}".rstrip("0").rstrip(".") + "kg"


def build_reference_body_html(product: Dict[str, Any]) -> str:
    """Build Body (HTML) using the fixed reference template with dynamic content only."""
    main_description = _html_paragraph_text(
        product.get("description_long") or product.get("description") or product.get("title", "")
    )

    details_blocks: List[str] = []
    designs_available = _escape_text(product.get("designs_available"))
    if designs_available:
        details_blocks.extend([
            "  <h5>Designs Available</h5>",
            f"  <p>{designs_available}</p>",
            "  <br>",
        ])

    fabric_colour = _escape_text(product.get("fabric_colour"))
    if fabric_colour:
        details_blocks.extend([
            "  <h5>Fabric Colour</h5>",
            f"  <p>{fabric_colour}</p>",
            "  <br>",
        ])

    height = _format_mm_to_cm(product.get("height_mm"))
    width = _format_mm_to_cm(product.get("width_mm"))
    depth = _format_mm_to_cm(product.get("depth_mm"))
    weight = _format_weight_kg(product.get("weight_display"))
    dimension_lines = []
    if height:
        dimension_lines.append(f"  <p>Height: {height}</p>")
    if width:
        dimension_lines.append(f"  <p>Width: {width}</p>")
    if depth:
        dimension_lines.append(f"  <p>Depth: {depth}</p>")
    if weight:
        dimension_lines.append(f"  <p>Weight: {weight}</p>")
    if dimension_lines:
        details_blocks.append("  <h5>Product Dimensions</h5>")
        details_blocks.extend(dimension_lines)
        details_blocks.append("  <br>")

    details_section = [
        "<button class=\"collapsible\">Details</button>",
        "<div class=\"content\">",
        "  <!-- These are where the variant details go -->",
    ]
    details_section.extend(details_blocks)
    details_section.append("</div>")

    certification_values = [
        _escape_text(val)
        for val in str(product.get("certifications") or "").split(",")
        if str(val).strip()
    ]
    certifications_section: List[str] = []
    if certification_values:
        certifications_section.extend([
            "<!-- This is for the certifications and warranties (not all products have both) if not, just removed-->",
            "<button class=\"collapsible\">Certifications</button>",
            "<div class=\"content\"> ",
            "  <h5>Certifications</h5>",
        ])
        for cert in certification_values:
            certifications_section.append(f"  <p>{cert}</p>")
        certifications_section.extend([
            "  <br> ",
            "</div>",
            "<br>",
        ])

    file_links = []
    care_guide_url = str(product.get("care_guide_url") or "").strip()
    assembly_instruction_url = str(product.get("assembly_instruction_url") or "").strip()
    if care_guide_url:
        file_links.append((care_guide_url, "Care and Maintenance"))
    if assembly_instruction_url:
        file_links.append((assembly_instruction_url, "Assembly instructions"))

    files_section: List[str] = []
    if file_links:
        files_section.extend([
            "<!-- This is for the files (not all products have) if not, just removed-->",
            "<button class=\"collapsible\">Files</button>",
            "<div class=\"content\">",
        ])
        for idx, (url, label) in enumerate(file_links):
            safe_url = html.escape(url, quote=True)
            safe_label = _escape_text(label)
            files_section.append(f"  <a href=\"{safe_url}\">{safe_label}")
            files_section.append("  </a>")
            if idx < len(file_links) - 1:
                files_section.append("  <br>")
        files_section.append("</div>")

    body_parts = [
        "<style>",
        "  .content-wrapper {",
        "    max-height: 100px;",
        "    overflow: hidden;",
        "    position: relative;",
        "    transition: max-height 0.3s ease-out;",
        "  }",
        "  ",
        "  .content-wrapper.expanded {",
        "    max-height: 500px;",
        "  }",
        "",
        "  .read-more-button {",
        "    display: block;",
        "    margin-top: 15px;",
        "    cursor: pointer;",
        "    color: #736357;",
        "  }",
        "  ",
        "  .collapsible {",
        "    background-color: #FBF9F7;",
        "    color: #736357;",
        "    cursor: pointer;",
        "    padding: 20px 0px;",
        "    width: 100%;",
        "    border: none;",
        "    text-align: left;",
        "    font-size: 15px;",
        "  }",
        "",
        "  .collapsible:after {",
        "    content: '\\002B';",
        "    color: #736357;",
        "    font-weight: bold;",
        "    float: right;",
        "    margin-left: 5px;",
        "  }",
        "",
        "  .active:after {",
        "    content: \"\\2212\";",
        "  }",
        "  ",
        "  .content {",
        "    padding: 0px 10px;",
        "    max-height: 0;",
        "    overflow: hidden;",
        "    transition: max-height 0.2s ease-out;",
        "    background-color: #FBF9F7;",
        "  }",
        "",
        "</style>",
        "<div id=\"myContent\" class=\"content-wrapper\">",
        "  <!-- This is the Product Description -->",
        f"  <p>{main_description}</p>",
        "</div>",
        "<span class=\"read-more-button\" onclick=\"toggleReadMore()\">+ More</span>",
        "<br><br>",
        "<!-- These are the dropdown tabs of information -->",
    ]

    body_parts.extend(details_section)
    body_parts.extend(certifications_section)
    body_parts.append("<br>")
    body_parts.extend(files_section)
    body_parts.extend([
        "<script>",
        "var coll = document.getElementsByClassName(\"collapsible\");",
        "var i;",
        "",
        "for (i = 0; i < coll.length; i++) {",
        "coll[i].addEventListener(\"click\", function() {",
        "this.classList.toggle(\"active\");",
        "var content = this.nextElementSibling;",
        "if (content.style.maxHeight){",
        "content.style.maxHeight = null;",
        "} else {",
        "content.style.maxHeight = content.scrollHeight + \"px\";",
        "}",
        "});",
        "}",
        "",
        "function toggleReadMore() {",
        "const content = document.getElementById('myContent');",
        "content.classList.toggle('expanded');",
        "const button = document.querySelector('.read-more-button');",
        "if (content.classList.contains('expanded')) {",
        "button.textContent = 'Show Less';",
        "} else {",
        "button.textContent = '+ More';",
        "}",
        "}",
        "</script>",
    ])

    return "\n".join(body_parts)


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
    body_html = build_reference_body_html(product)

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
