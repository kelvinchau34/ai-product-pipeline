"""Optional Shopify API upload module for direct product creation."""

from __future__ import annotations

import base64
import os
from io import BytesIO
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv
from PIL import Image


def get_shopify_config() -> Dict[str, str]:
    """
    Load Shopify API credentials from environment.

    Returns:
        Dict with store URL and access token
    """
    load_dotenv()
    return {
        "store": os.getenv("SHOPIFY_STORE", ""),
        "token": os.getenv("SHOPIFY_ACCESS_TOKEN", ""),
        "api_version": "2024-04",
    }


def process_image_from_url(url: str, max_pixels: int = 25000000) -> Dict[str, Any]:
    """
    Download, resize, and encode image to base64.

    Args:
        url: Image URL
        max_pixels: Maximum pixel count before resizing

    Returns:
        Dict with:
            - success (bool)
            - encoded (str): Base64 encoded image data
            - format (str): Image format (JPEG or PNG)
            - error (str): Error message if failed
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))

        # Resize if too large
        if img.width * img.height > max_pixels:
            scale = (max_pixels / float(img.width * img.height)) ** 0.5
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.LANCZOS)

        # Encode to base64
        buffer = BytesIO()
        img_format = "JPEG" if img.mode in ("RGB", "L") else "PNG"
        img.save(buffer, format=img_format, quality=85)
        buffer.seek(0)

        encoded = base64.b64encode(buffer.read()).decode("utf-8")

        return {
            "success": True,
            "encoded": encoded,
            "format": img_format,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "encoded": "",
            "format": "",
            "error": f"Failed to process image: {str(e)}",
        }


def build_product_payload(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build Shopify API product payload from product data.

    Args:
        product: Normalized product dict

    Returns:
        Shopify API product payload
    """
    # Build variants
    variants = [
        {
            "price": str(product.get("price", "0.00")),
            "sku": product.get("sku", ""),
            "grams": int(product.get("grams", 0)),
            "weight_unit": product.get("weight_unit", "kg"),
            "inventory_policy": "deny",
            "fulfillment_service": "manual",
            "requires_shipping": True,
            "taxable": True,
            "barcode": product.get("barcode", ""),
        }
    ]

    # Build images list
    images = []
    seen_images = set()
    position = 1

    for image_url in product.get("images", []):
        if image_url and image_url not in seen_images:
            result = process_image_from_url(image_url)
            if result["success"]:
                images.append({
                    "attachment": result["encoded"],
                    "position": position,
                    "alt": product.get("image_alt_text", product.get("title", "")),
                })
                position += 1
                seen_images.add(image_url)

    return {
        "product": {
            "title": product.get("title", ""),
            "body_html": product.get("body_html", ""),
            "vendor": product.get("vendor", ""),
            "product_type": product.get("product_type", ""),
            "tags": product.get("tags", ""),
            "status": "draft",
            "variants": variants,
            "images": images,
        }
    }


def upload_product(product: Dict[str, Any], config: Dict[str, str] | None = None) -> Dict[str, Any]:
    """
    Upload a single product to Shopify API.

    Args:
        product: Normalized product dict
        config: Shopify config dict (uses environment if not provided)

    Returns:
        Dict with:
            - success (bool)
            - product_id (str): Shopify product ID
            - title (str): Product title
            - error (str): Error message if failed
    """
    if not config:
        config = get_shopify_config()

    if not config["store"] or not config["token"]:
        return {
            "success": False,
            "product_id": "",
            "title": product.get("title", ""),
            "error": "Shopify credentials not configured",
        }

    try:
        payload = build_product_payload(product)

        base_url = f"https://{config['store']}/admin/api/{config['api_version']}/products.json"
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": config["token"],
        }

        response = requests.post(base_url, json=payload, headers=headers, timeout=30)

        if response.status_code == 201:
            data = response.json()
            product_id = data.get("product", {}).get("id", "")
            return {
                "success": True,
                "product_id": str(product_id),
                "title": product.get("title", ""),
                "error": None,
            }
        else:
            return {
                "success": False,
                "product_id": "",
                "title": product.get("title", ""),
                "error": f"API error {response.status_code}: {response.text}",
            }
    except Exception as e:
        return {
            "success": False,
            "product_id": "",
            "title": product.get("title", ""),
            "error": f"Upload failed: {str(e)}",
        }


def upload_products(products: List[Dict[str, Any]], config: Dict[str, str] | None = None) -> Dict[str, Any]:
    """
    Upload multiple products to Shopify API.

    Args:
        products: List of normalized product dicts
        config: Shopify config dict

    Returns:
        Dict with:
            - success (bool)
            - uploaded_count (int)
            - failed_count (int)
            - results (list): Upload results for each product
            - error (str): Overall error message
    """
    if not config:
        config = get_shopify_config()

    results = []
    uploaded_count = 0
    failed_count = 0

    for product in products:
        result = upload_product(product, config)
        results.append(result)

        if result["success"]:
            uploaded_count += 1
        else:
            failed_count += 1

    return {
        "success": failed_count == 0,
        "uploaded_count": uploaded_count,
        "failed_count": failed_count,
        "results": results,
        "error": None if failed_count == 0 else f"{failed_count} products failed to upload",
    }
