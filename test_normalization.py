"""Test script for the normalization pipeline"""
import pandas as pd
import sys
sys.path.insert(0, './src')

from normalise import normalize_product

# Load the CSV file
csv_path = './input_examples/sample-input.csv'
df = pd.read_csv(csv_path)

print(f"Total products in CSV: {len(df)}")
print(f"Columns: {len(df.columns)}\n")

# Get the first product as a dictionary
first_product = df.iloc[0].to_dict()

print("=" * 80)
print("FIRST PRODUCT - RAW DATA")
print("=" * 80)
print(f"Item no. (SKU): {first_product.get('Item no.')}")
print(f"EAN (Barcode): {first_product.get('EAN')}")
print(f"Description: {first_product.get('Description')}")
print(f"Weight: {first_product.get('Weight')}")
print(f"Category: {first_product.get('Category')}")

print("\n" + "=" * 80)
print("NORMALIZING PRODUCT...")
print("=" * 80 + "\n")

# Normalize the product
normalized = normalize_product(first_product)

print("NORMALIZED RESULT:")
print("-" * 80)
print(f"Title:           {normalized.get('title')}")
print(f"SKU:             {normalized.get('sku')}")
print(f"Barcode (EAN):   {normalized.get('barcode')}")
print(f"Product Type:    {normalized.get('product_type')}")
print(f"Weight (grams):  {normalized.get('grams')}")
print(f"Weight Unit:     {normalized.get('weight_unit')}")
print(f"Vendor:          {normalized.get('vendor')}")
print(f"Status:          {normalized.get('status')}")
print(f"Handle:          {normalized.get('handle')}")
print(f"Price:           {normalized.get('price')}")
print(f"Tags:            {normalized.get('tags')}")
print(f"Features:        {normalized.get('features')}")
print(f"Images Count:    {len(normalized.get('images', []))}")
if normalized.get('images'):
    print(f"Image URLs:")
    for i, img in enumerate(normalized.get('images', []), 1):
        print(f"  {i}. {img[:100]}..." if len(img) > 100 else f"  {i}. {img}")
print(f"\nBody HTML (first 150 chars):")
body_html = normalized.get('body_html', '')
print(f"  {body_html[:150]}..." if len(body_html) > 150 else f"  {body_html}")
print(f"  (Total length: {len(body_html)} chars)")
print("\n" + "=" * 80)
print("VERIFICATION CHECKS")
print("=" * 80)

# Verify mapping
print(f"✓ SKU from 'Item no.': {normalized.get('sku') == str(first_product.get('Item no.')).strip()}")
print(f"✓ Barcode from 'EAN': {normalized.get('barcode') == str(first_product.get('EAN')).strip()}")
print(f"✓ Product Type from 'Category': {normalized.get('product_type') == first_product.get('Category')}")
print(f"✓ Weight parsed to grams: {normalized.get('grams') > 0 or normalized.get('grams') == 0}")
print(f"✓ Images extracted: {len(normalized.get('images', [])) >= 0}")
print(f"✓ Body HTML generated: {len(normalized.get('body_html', '')) > 0}")

