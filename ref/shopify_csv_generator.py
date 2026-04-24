import json
import csv
import re
from typing import List, Dict

class ShopifyCSVGenerator:
    def __init__(self):
        # Shopify CSV headers as specified
        self.headers = [
            'Handle', 'Title', 'Body (HTML)', 'Vendor', 'Product Category', 'Type', 'Tags', 
            'Published', 'Option1 Name', 'Option1 Value', 'Option2 Name', 'Option2 Value', 
            'Option3 Name', 'Option3 Value', 'Variant SKU', 'Variant Grams', 
            'Variant Inventory Tracker', 'Variant Inventory Qty', 'Variant Inventory Policy', 
            'Variant Fulfillment Service', 'Variant Price', 'Variant Compare At Price', 
            'Variant Requires Shipping', 'Variant Taxable', 'Variant Barcode', 'Image Src', 
            'Image Position', 'Image Alt Text', 'Gift Card', 'SEO Title', 'SEO Description', 
            'Google Shopping / Google Product Category', 'Google Shopping / Gender', 
            'Google Shopping / Age Group', 'Google Shopping / MPN', 'Google Shopping / Condition', 
            'Google Shopping / Custom Product', 'Variant Image', 'Variant Weight Unit', 
            'Variant Tax Code', 'Cost per item', 'Included / United States', 
            'Price / United States', 'Compare At Price / United States', 
            'Included / International', 'Price / International', 
            'Compare At Price / International', 'Status'
        ]
        
        # Default values as specified
        self.defaults = {
            'Vendor': 'M&E Interior',
            'Product Category': 'Uncategory',
            'Published': 'FALSE',
            'Variant Grams': '0',
            'Variant Inventory Policy': 'deny',
            'Variant Fulfillment Service': 'manual',
            'Variant Price': '0',
            'Variant Requires Shipping': 'FALSE',
            'Variant Taxable': 'TRUE',
            'Gift Card': 'FALSE',
            'Variant Weight Unit': 'kg',
            'Status': 'draft'
        }
    
    def create_handle(self, title: str) -> str:
        """Convert product title to Shopify handle format"""
        # Convert to lowercase and replace spaces with hyphens
        handle = title.lower()
        # Remove special characters except letters, numbers, spaces, and hyphens
        handle = re.sub(r'[^\w\s-]', '', handle)
        # Replace multiple spaces or hyphens with single hyphen
        handle = re.sub(r'[-\s]+', '-', handle)
        # Remove leading/trailing hyphens
        handle = handle.strip('-')
        return handle
    
    def detect_product_type(self, title: str, description: str) -> str:
        """Detect product type from title and description"""
        text = (title + ' ' + description).lower()
        
        # Define product type keywords
        type_keywords = {
            'dining chair': ['dining chair', 'side chair'],
            'lounge chair': ['lounge chair', 'armchair', 'accent chair'],
            'bar stool': ['bar stool', 'barstool', 'counter stool'],
            'dining table': ['dining table', 'table'],
            'coffee table': ['coffee table', 'cocktail table'],
            'side table': ['side table', 'end table', 'accent table'],
            'sofa': ['sofa', 'couch', 'sectional'],
            'bench': ['bench', 'seating bench'],
            'stool': ['stool'],
            'chair': ['chair']  # Generic fallback
        }
        
        # Check for specific types first, then general
        for product_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return product_type
        
        return 'furniture'  # Default fallback
    
    def format_description_as_html(self, description: str, dimensions: str, features: List[str]) -> str:
        """Format product description as HTML"""
        html_parts = []
        
        if description:
            html_parts.append(f"<p>{description}</p>")
        
        if dimensions:
            html_parts.append(f"<p><strong>Dimensions:</strong> {dimensions}</p>")
        
        if features:
            html_parts.append("<p><strong>Features:</strong></p>")
            html_parts.append("<ul>")
            for feature in features:
                # Clean up feature text
                feature_clean = feature.strip('- •').strip()
                if feature_clean:
                    html_parts.append(f"<li>{feature_clean}</li>")
            html_parts.append("</ul>")
        
        return '\n'.join(html_parts)
    
    def create_main_product_row(self, product: Dict) -> Dict:
        """Create the main product row"""
        handle = self.create_handle(product['title'])
        product_type = self.detect_product_type(product['title'], product.get('description', ''))
        body_html = self.format_description_as_html(
            product.get('description', ''),
            product.get('dimensions', ''),
            product.get('features', [])
        )
        
        row = {header: '' for header in self.headers}  # Initialize all columns as empty
        
        # Fill in the specified values
        row.update(self.defaults)
        row.update({
            'Handle': handle,
            'Title': product['title'],
            'Body (HTML)': body_html,
            'Type': product_type,
            'Tags': product_type,
            'Variant SKU': product.get('sku', ''),
            'SEO Title': product['title'],
            'SEO Description': product.get('description', '')[:160]  # SEO desc should be max 160 chars
        })
        
        # Add first image if available
        if product.get('images') and len(product['images']) > 0:
            row['Image Src'] = product['images'][0]
            row['Image Position'] = '1'
            row['Image Alt Text'] = product['title']
        
        return row
    
    def create_image_rows(self, product: Dict, handle: str) -> List[Dict]:
        """Create additional rows for extra images"""
        image_rows = []
        
        # Skip first image (already in main row) and create rows for remaining images
        for i, image_url in enumerate(product.get('images', [])[1:], start=2):
            row = {header: '' for header in self.headers}
            row.update({
                'Handle': handle,
                'Image Src': image_url,
                'Image Position': str(i),
                'Image Alt Text': product['title']
            })
            image_rows.append(row)
        
        return image_rows
    
    def generate_csv_data(self, products_data: List[Dict]) -> List[Dict]:
        """Generate complete CSV data for all products"""
        csv_rows = []
        
        for product in products_data:
            if not product.get('title'):
                continue  # Skip products without titles
            
            # Create main product row
            main_row = self.create_main_product_row(product)
            csv_rows.append(main_row)
            
            # Create additional image rows
            handle = main_row['Handle']
            image_rows = self.create_image_rows(product, handle)
            csv_rows.extend(image_rows)
        
        return csv_rows
    
    def save_to_csv(self, products_data: List[Dict], filename: str = 'shopify_import.csv'):
        """Save product data to Shopify CSV format"""
        csv_data = self.generate_csv_data(products_data)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.headers)
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(f"Shopify CSV saved to {filename}")
        print(f"Total rows: {len(csv_data)}")
        
        # Print summary
        main_products = len([row for row in csv_data if row['Image Position'] == '1' or row['Image Position'] == ''])
        image_rows = len(csv_data) - main_products
        print(f"Products: {main_products}")
        print(f"Additional image rows: {image_rows}")
        
        return csv_data
    
    def load_scraped_data(self, json_filename: str) -> List[Dict]:
        """Load data from the scraping script's JSON output"""
        try:
            with open(json_filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: File {json_filename} not found")
            return []
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {json_filename}")
            return []
    
    def preview_data(self, products_data: List[Dict], num_products: int = 3):
        """Preview how the data will look in the CSV"""
        csv_data = self.generate_csv_data(products_data[:num_products])
        
        print(f"\nPreview of first {num_products} products:")
        print("-" * 50)
        
        for i, row in enumerate(csv_data):
            if row['Image Position'] == '1' or row['Image Position'] == '':
                print(f"\nProduct: {row['Title']}")
                print(f"Handle: {row['Handle']}")
                print(f"Type: {row['Type']}")
                print(f"SKU: {row['Variant SKU']}")
                print(f"Image: {row['Image Src'][:50]}..." if row['Image Src'] else "No image")
            else:
                print(f"  Additional image {row['Image Position']}: {row['Image Src'][:50]}...")

# Usage functions
def main():
    generator = ShopifyCSVGenerator()
    
    # Load scraped data
    json_file = input("Enter JSON filename (default: billiani_collection.json): ").strip()
    if not json_file:
        json_file = "billiani_collection.json"
    
    products_data = generator.load_scraped_data(json_file)
    
    if not products_data:
        print("No product data found. Make sure to run the scraper first.")
        return
    
    print(f"Loaded {len(products_data)} products")
    
    # Preview data
    preview = input("Preview data? (y/n, default: y): ").strip().lower()
    if preview != 'n':
        generator.preview_data(products_data)
    
    # Generate CSV
    csv_filename = input("\nEnter CSV filename (default: shopify_import.csv): ").strip()
    if not csv_filename:
        csv_filename = "shopify_import.csv"
    
    generator.save_to_csv(products_data, csv_filename)
    
    print(f"\nDone! Import {csv_filename} into Shopify.")
    print("Note: You may want to review and adjust prices, inventory quantities, and other details before importing.")

if __name__ == "__main__":
    main()