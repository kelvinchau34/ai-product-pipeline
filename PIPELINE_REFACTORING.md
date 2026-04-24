# Pipeline Refactoring Guide

## Overview

The original scripts (`ref/photo_process.py` and `ref/shopify_csv_generator.py`) have been refactored into a clean, modular pipeline suitable for AWS Lambda deployment and incremental testing.

## Architecture

### Module Breakdown

#### 1. **src/ingest.py** - Data Loading

- `load_csv(filepath)` - Load CSV data
- `load_json(filepath)` - Load JSON data
- `load_data(filepath)` - Auto-detect format and load

**Returns:** Structured dict with `success`, `records`, `count`, `error`

#### 2. **src/normalise.py** - Data Standardization

- `normalize_product(record)` - Normalize single record to standard fields
- `normalize_records(records)` - Normalize list of records

**Key changes from original:**

- Handles both CSV and JSON field naming conventions
- Returns structured result instead of just printing

#### 3. **src/validate.py** - Data Validation

- `validate_product(record)` - Validate single product
- `validate_records(records)` - Validate list, separating valid/invalid

**Validates:**

- Required fields: `title`, `sku`
- Price must be numeric
- Grams must be numeric

#### 4. **src/exporter.py** - Shopify CSV Generation

Extracted from `ShopifyCSVGenerator` class:

- `create_handle(title)` - Format title as Shopify handle
- `detect_product_type(title, description)` - Infer product type
- `format_description_as_html(description, dimensions, features)` - HTML formatting
- `generate_csv_data(products)` - Generate complete CSV rows
- `export_to_csv(products, filepath)` - Write CSV file

**Returns:** Structured result with file path, product count, row count

#### 5. **src/ai_enhancer.py** - Optional AI Enhancement

- `enhance_product(record, provider)` - Enhance single product
- `enhance_records(records, provider)` - Enhance list (placeholder for future implementation)

**Provider options:**

- `None` - Skip enhancement
- `"openai"` - OpenAI API (not yet implemented)
- `"bedrock"` - AWS Bedrock (not yet implemented)

#### 6. **src/uploader.py** - Shopify API Upload

Extracted from `photo_process.py`:

- `process_image_from_url(url)` - Download and resize image to base64
- `build_product_payload(product)` - Format product for Shopify API
- `upload_product(product, config)` - Upload single product
- `upload_products(products, config)` - Upload multiple products

**Key changes:**

- Completely optional (no interactive prompts)
- Reads credentials from environment variables
- Returns structured results with success/failure details
- Errors don't break the pipeline

#### 7. **src/pipeline.py** - Main Orchestrator

- `process_products()` - Run complete pipeline
- `process_with_config()` - Run with config dict

**Stages:**

1. Ingest
2. Normalize
3. Validate
4. AI Enhance (optional)
5. Export CSV (optional)
6. Upload to Shopify (optional)

## Key Improvements Over Original Scripts

| Aspect             | Before                  | After                       |
| ------------------ | ----------------------- | --------------------------- |
| **Input**          | `input()` prompts       | Function parameters         |
| **Output**         | Print statements        | Structured dicts            |
| **Error handling** | Crashes/uncaught errors | Graceful error returns      |
| **Reusability**    | Hardcoded file paths    | Parameterized functions     |
| **Testing**        | Not testable            | Comprehensive test suite    |
| **Optionality**    | Forced Shopify upload   | All uploads optional        |
| **Configuration**  | Hard to configure       | Environment + function args |

## Usage Examples

### Simple: Process CSV to Shopify CSV

```python
from src import pipeline

result = pipeline.process_products(
    filepath="data/products.csv",
    export_csv=True,
    output_csv_path="output/shopify_import.csv",
    upload_to_shopify=False,
)

print(result["final_summary"])
```

### Advanced: Inspect Validation Results

```python
from src import ingest, normalise, validate

# Load
data = ingest.load_csv("input.csv")
records = data["records"]

# Normalize
norm = normalise.normalize_records(records)
normalized = norm["records"]

# Validate and inspect
val = validate.validate_records(normalized)
print(f"Valid: {val['valid_count']}")
for invalid in val["invalid_records"]:
    print(f"  Row {invalid['index']}: {invalid['errors']}")
```

### With Optional Shopify Upload

```python
result = pipeline.process_products(
    filepath="data/products.csv",
    export_csv=True,
    output_csv_path="output/shopify.csv",
    upload_to_shopify=True,  # Requires SHOPIFY_STORE and SHOPIFY_ACCESS_TOKEN in .env
    ai_provider=None,
)

if "upload" in result["stages"]:
    upload_result = result["stages"]["upload"]
    print(f"Uploaded: {upload_result['uploaded_count']}")
```

## Running Tests

```bash
# All tests
pytest -v

# Unit tests only
pytest tests/test_transform.py -v

# Integration tests
pytest tests/test_integration.py -v

# With coverage
pytest --cov=src tests/
```

## Running Examples

```bash
python examples.py
```

## Environment Configuration

Copy `.env.example` to `.env` and fill values:

```
AWS_REGION=ap-southeast-1
INPUT_BUCKET=product-pipeline-input
OUTPUT_BUCKET=product-pipeline-output
LOG_LEVEL=INFO

# Optional: for Shopify uploads
SHOPIFY_STORE=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shppa_...

# Optional: for AI enhancement
OPENAI_API_KEY=sk-...
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

## Lambda Integration

The `src/pipeline.py` is ready for AWS Lambda:

```python
# lambda_function.py
from src import pipeline

def lambda_handler(event, context):
    """Lambda handler for product processing."""
    return pipeline.process_products(
        filepath=event.get("input_file"),
        export_csv=event.get("export_csv", True),
        output_csv_path=event.get("output_csv_path"),
        upload_to_shopify=event.get("upload_shopify", False),
        ai_provider=event.get("ai_provider"),
    )
```

## Future Enhancements

1. **AI Enhancement** - Connect OpenAI/Bedrock APIs
2. **S3 Integration** - Direct read/write to S3 buckets
3. **Async Uploads** - Queue Shopify uploads with SQS
4. **Batch Processing** - Handle large datasets with Step Functions
5. **Validation Rules** - Configurable validation per product type
6. **Progress Tracking** - Store pipeline progress in DynamoDB

## Migration from Original Scripts

### From `shopify_csv_generator.py`:

```python
# Old
generator = ShopifyCSVGenerator()
products = generator.load_scraped_data("data.json")
generator.save_to_csv(products, "output.csv")

# New
from src import ingest, normalise, validate, exporter
data = ingest.load_json("data.json")
norm = normalise.normalize_records(data["records"])
val = validate.validate_records(norm["records"])
exporter.export_to_csv(val["valid_records"], "output.csv")
```

### From `photo_process.py`:

```python
# Old
for handle, group in df.groupby("Handle"):
    create_product(group)

# New
from src import uploader
result = uploader.upload_products(products)
```
