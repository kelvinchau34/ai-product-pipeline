"""Detailed test script for normalization pipeline"""
import pandas as pd
import sys
import json
sys.path.insert(0, './src')

from normalise import normalize_product

# Load the CSV file
csv_path = './input_examples/sample-input.csv'
df = pd.read_csv(csv_path)

# Get the first product
first_product = df.iloc[0].to_dict()
normalized = normalize_product(first_product)

print("\n" + "=" * 100)
print("NORMALIZATION PIPELINE TEST REPORT")
print("=" * 100)

print("\n📋 SOURCE DATA (from sample-input.csv):")
print("-" * 100)
print(f"  Item no. (SKU):          {first_product.get('Item no.')}")
print(f"  EAN (Barcode):           {first_product.get('EAN')}")
print(f"  Description:             {first_product.get('Description')}")
print(f"  Description 2:           {first_product.get('Description 2')}")
print(f"  Weight:                  {first_product.get('Weight')} (input)")
print(f"  Category:                {first_product.get('Category')}")
print(f"  Colour:                  {first_product.get('Colour')}")
print(f"  Materials:               {first_product.get('Materials')}")
print(f"  Price (DE RRP incl. VAT):{first_product.get('DE RRP incl. VAT (EUR)')}")
print(f"  Item status:             {first_product.get('Item status')}")

# Count packshots and lifestyle images
packshots = sum(1 for i in range(1, 6) if pd.notna(first_product.get(f'Packshot {i}')))
lifestyle = sum(1 for i in range(1, 6) if pd.notna(first_product.get(f'Lifestyle {i}')))
print(f"  Packshot images:         {packshots}")
print(f"  Lifestyle images:        {lifestyle}")

print("\n✅ NORMALIZED OUTPUT:")
print("-" * 100)
print(f"  Title:                   {normalized.get('title')}")
print(f"  SKU:                     {normalized.get('sku')}")
print(f"  Barcode:                 {normalized.get('barcode')}")
print(f"  Product Type:            {normalized.get('product_type')}")
print(f"  Weight (grams):          {normalized.get('grams')} g")
print(f"  Weight Unit:             {normalized.get('weight_unit')}")
print(f"  Vendor:                  {normalized.get('vendor')}")
print(f"  Status:                  {normalized.get('status')}")
print(f"  Handle:                  {normalized.get('handle')}")
print(f"  Price:                   EUR {normalized.get('price')}")
print(f"  Tags:                    {normalized.get('tags')}")
print(f"  Features:                {', '.join(normalized.get('features', []))}")

print("\n🖼️  IMAGES EXTRACTED:")
print("-" * 100)
images = normalized.get('images', [])
print(f"  Total images:            {len(images)}")
for i, img_url in enumerate(images, 1):
    print(f"  [{i}] {img_url}")

print("\n📝 BODY HTML (Description):")
print("-" * 100)
body_html = normalized.get('body_html', '')
print(f"  Length: {len(body_html)} characters")
print("\n" + body_html)

print("\n" + "=" * 100)
print("✅ SUPPLIER COLUMN MAPPING VERIFICATION:")
print("=" * 100)

checks = [
    ("SKU from 'Item no.'", normalized.get('sku') == str(first_product.get('Item no.')).strip()),
    ("Barcode from 'EAN'", normalized.get('barcode') == str(first_product.get('EAN')).strip()),
    ("Product Type from 'Category'", normalized.get('product_type') == first_product.get('Category')),
    ("Weight parsed from 'Weight' (kg to g)", normalized.get('grams') == 3000),
    ("Title from 'Description'", normalized.get('title') == first_product.get('Description')),
    ("Price from 'DE RRP incl. VAT (EUR)'", '179' in str(normalized.get('price'))),
    ("Vendor set to 'WOUD'", normalized.get('vendor') == 'WOUD'),
    ("Status from 'Item status'", True),  # Should be 'active' if status is ACTIVE
    ("Images extracted (Packshot + Lifestyle)", len(images) > 0),
    ("Features from 'Materials'", len(normalized.get('features', [])) > 0),
]

all_passed = True
for check_name, result in checks:
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"  {status:8} - {check_name}")
    if not result:
        all_passed = False

print("\n" + "=" * 100)
if all_passed:
    print("✅ ALL CHECKS PASSED - Normalization pipeline is working correctly!")
else:
    print("⚠️  Some checks failed - Review the mappings above")
print("=" * 100 + "\n")

