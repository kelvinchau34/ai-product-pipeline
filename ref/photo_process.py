import os
import math
import json
import base64
import tempfile
import requests
import pandas as pd
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

# --------------------------
# Load Shopify credentials
# --------------------------
load_dotenv()
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

API_VERSION = "2024-04"
BASE_URL = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/products.json"
HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": ACCESS_TOKEN
}

def clean_value(val, default=None):
    if pd.isna(val) or (isinstance(val, float) and math.isnan(val)):
        return default
    return val

# --------------------------
# Resize + Encode Image
# --------------------------
def process_image_from_url(url, max_pixels=25000000):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))

        # Check if image exceeds pixel count
        if img.width * img.height > max_pixels:
            scale = (max_pixels / float(img.width * img.height)) ** 0.5
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.LANCZOS)

        # Save to bytes in JPEG/PNG
        buffer = BytesIO()
        img_format = "JPEG" if img.mode in ("RGB", "L") else "PNG"
        img.save(buffer, format=img_format, quality=85)
        buffer.seek(0)

        # Encode to base64 for Shopify API
        encoded = base64.b64encode(buffer.read()).decode("utf-8")
        return encoded

    except Exception as e:
        print(f"⚠️ Failed to process image {url}: {e}")
        return None

# --------------------------
# Load CSV
# --------------------------
csv_path = "19-9-2025.csv"
df = pd.read_csv(csv_path)
df = df.dropna(subset=["Handle"])

# --------------------------
# Build and upload products
# --------------------------
def create_product(handle_group):
    first_row = handle_group.iloc[0].to_dict()

    # Variant setup
    variants = [{
        "price": str(clean_value(first_row.get("Variant Price"), "0.00")),
        "sku": clean_value(first_row.get("Variant SKU")),
        "grams": int(clean_value(first_row.get("Variant Grams"), 0)),
        "weight_unit": clean_value(first_row.get("Variant Weight Unit"), "g"),
        "inventory_policy": clean_value(first_row.get("Variant Inventory Policy"), "deny"),
        "fulfillment_service": clean_value(first_row.get("Variant Fulfillment Service"), "manual"),
        "requires_shipping": bool(clean_value(first_row.get("Variant Requires Shipping"), True)),
        "taxable": bool(clean_value(first_row.get("Variant Taxable"), True)),
        "barcode": clean_value(first_row.get("Variant Barcode"))
    }]

    # Collect & resize images
    images = []
    seen_images = set()
    position_counter = 1

    for _, row in handle_group.iterrows():
        img_src = clean_value(row.get("Image Src"))
        if img_src and img_src not in seen_images:
            encoded_img = process_image_from_url(img_src)
            if encoded_img:
                images.append({
                    "attachment": encoded_img,
                    "position": position_counter,
                    "alt": clean_value(row.get("Image Alt Text"))
                })
                position_counter += 1
                seen_images.add(img_src)

    print(f"\nImages collected for {first_row['Title']}: {len(images)}")

    # Product payload
    product_data = {
        "product": {
            "title": first_row["Title"],
            "body_html": clean_value(first_row.get("Body (HTML)"), ""),
            "vendor": clean_value(first_row.get("Vendor"), "Default Vendor"),
            "product_type": clean_value(first_row.get("Type"), "General"),
            "tags": clean_value(first_row.get("Tags"), ""),
            "status": clean_value(first_row.get("Status"), "draft"),
            "variants": variants,
            "images": images
        }
    }

    print(f"\nUploading product: {first_row['Title']}")
    response = requests.post(BASE_URL, json=product_data, headers=HEADERS)
    if response.status_code == 201:
        print(f"✅ Created product: {first_row['Title']}")
    else:
        print(f"❌ Failed: {first_row['Title']} - {response.status_code} {response.text}")


# --------------------------
# Run
# --------------------------
for handle, group in df.groupby("Handle"):
    create_product(group)
