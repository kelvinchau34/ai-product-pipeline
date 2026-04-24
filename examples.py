"""Example usage of the modular pipeline."""

from __future__ import annotations

import json

from src import ingest, normalise, validate, ai_enhancer, exporter, uploader, pipeline


def example_1_basic_pipeline() -> None:
    """Example 1: Run the complete pipeline with default settings."""
    print("=== Example 1: Basic Pipeline ===\n")

    result = pipeline.process_products(
        filepath="input_examples/sample-input.csv",
        export_csv=True,
        output_csv_path="output/shopify_import.csv",
        upload_to_shopify=False,  # Keep False unless Shopify is configured
    )

    print(f"Success: {result['success']}")
    print(f"Total input: {result['final_summary']['total_input']}")
    print(f"Successfully processed: {result['final_summary']['successfully_processed']}")
    print(f"Exported: {result['final_summary']['exported']}\n")


def example_2_with_validation_inspection() -> None:
    """Example 2: Inspect validation results to see invalid records."""
    print("=== Example 2: Validation Inspection ===\n")

    # Step 1: Ingest
    ingest_result = ingest.load_csv("input_examples/sample-input.csv")
    if not ingest_result["success"]:
        print(f"Error: {ingest_result['error']}")
        return

    records = ingest_result["records"]
    print(f"Loaded {len(records)} records\n")

    # Step 2: Normalize
    normalize_result = normalise.normalize_records(records)
    normalized = normalize_result["records"]
    print(f"Normalized {len(normalized)} records\n")

    # Step 3: Validate and inspect
    validate_result = validate.validate_records(normalized)
    print(f"Valid: {validate_result['valid_count']}")
    print(f"Invalid: {validate_result['invalid_count']}\n")

    if validate_result["invalid_records"]:
        print("Invalid records:")
        for invalid in validate_result["invalid_records"]:
            print(f"  Index {invalid['index']}: {invalid['errors']}")


def example_3_incremental_processing() -> None:
    """Example 3: Process step by step for debugging."""
    print("=== Example 3: Incremental Processing ===\n")

    # Load
    ingest_result = ingest.load_json("input_examples/sample_input.json")
    if not ingest_result["success"]:
        # Try CSV as fallback
        ingest_result = ingest.load_csv("input_examples/sample-input.csv")

    if not ingest_result["success"]:
        print(f"Error: {ingest_result['error']}")
        return

    records = ingest_result["records"]
    print(f"1. Ingested: {ingest_result['count']} records")

    # Normalize
    norm_result = normalise.normalize_records(records)
    normalized = norm_result["records"]
    print(f"2. Normalized: {norm_result['count']} records")

    # Validate
    val_result = validate.validate_records(normalized)
    valid_records = val_result["valid_records"]
    print(f"3. Valid: {val_result['valid_count']}, Invalid: {val_result['invalid_count']}")

    # Enhance (optional)
    enh_result = ai_enhancer.enhance_records(valid_records, provider=None)
    enhanced = enh_result["records"]
    print(f"4. Enhanced: {enh_result['enhanced_count']}, Skipped: {enh_result['skipped_count']}")

    # Export
    exp_result = exporter.export_to_csv(enhanced, "output/example_3_output.csv")
    if exp_result["success"]:
        print(f"5. Exported: {exp_result['product_count']} products to {exp_result['filepath']}")
    else:
        print(f"5. Export failed: {exp_result['error']}")


def example_4_optional_shopify_upload() -> None:
    """Example 4: Upload to Shopify (requires credentials in .env)."""
    print("=== Example 4: Optional Shopify Upload ===\n")

    # Run full pipeline but enable upload
    result = pipeline.process_products(
        filepath="input_examples/sample-input.csv",
        export_csv=True,
        output_csv_path="output/shopify_import_upload.csv",
        upload_to_shopify=True,  # Enable upload
        ai_provider=None,
    )

    if "upload" in result["stages"]:
        upload_result = result["stages"]["upload"]
        print(f"Uploaded: {upload_result['uploaded_count']}")
        print(f"Failed: {upload_result['failed_count']}")
        if upload_result["results"]:
            print("\nUpload details:")
            for res in upload_result["results"]:
                status = "✓" if res["success"] else "✗"
                print(f"  {status} {res['title']}")


def example_5_ai_enhancement() -> None:
    """Example 5: Include AI enhancement in pipeline (placeholder)."""
    print("=== Example 5: AI Enhancement ===\n")

    result = pipeline.process_products(
        filepath="input_examples/sample-input.csv",
        export_csv=True,
        output_csv_path="output/shopify_import_ai.csv",
        upload_to_shopify=False,
        ai_provider="openai",  # When implemented, this will enhance descriptions
    )

    enh_result = result["stages"]["ai_enhance"]
    print(f"Enhanced: {enh_result['enhanced_count']}")
    print(f"Error: {enh_result['error']}")


def example_6_using_config_dict() -> None:
    """Example 6: Run pipeline with configuration dictionary."""
    print("=== Example 6: Config Dict ===\n")

    config = {
        "input_file": "input_examples/sample-input.csv",
        "output_csv": "output/config_example.csv",
        "export_csv": True,
        "upload_shopify": False,
        "ai_provider": None,
    }

    result = pipeline.process_with_config(config)
    print(f"Success: {result['success']}")
    print(f"Processed: {result['final_summary']['successfully_processed']}/{result['final_summary']['total_input']}")


if __name__ == "__main__":
    print("Pipeline Usage Examples\n")
    print("=" * 50 + "\n")

    try:
        example_1_basic_pipeline()
        print("\n" + "-" * 50 + "\n")

        example_2_with_validation_inspection()
        print("\n" + "-" * 50 + "\n")

        example_3_incremental_processing()
        print("\n" + "-" * 50 + "\n")

        print("Examples 4-6 require Shopify credentials or are advanced usage.")
        print("See code comments for details on how to use them.\n")

    except Exception as e:
        print(f"Error: {e}")
