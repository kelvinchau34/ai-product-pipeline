"""Integration tests for the complete pipeline."""

from pathlib import Path
import tempfile
import json
import csv

from src import pipeline


def test_pipeline_with_csv_input() -> None:
    """Pipeline should process CSV input and generate results."""
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "sku", "price", "description"])
        writer.writeheader()
        writer.writerow({
            "title": "Sample Chair",
            "sku": "CHAIR-001",
            "price": "129.99",
            "description": "A comfortable chair",
        })
        writer.writerow({
            "title": "Sample Table",
            "sku": "TABLE-001",
            "price": "249.99",
            "description": "A sturdy table",
        })
        temp_csv = f.name

    try:
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_output = f.name

        # Run pipeline
        result = pipeline.process_products(
            filepath=temp_csv,
            export_csv=True,
            output_csv_path=temp_output,
            upload_to_shopify=False,
        )

        # Verify results
        assert result["success"] is True
        assert result["final_summary"]["total_input"] == 2
        assert result["final_summary"]["successfully_processed"] == 2
        assert result["final_summary"]["exported"] is True

        # Verify CSV was created
        output_path = Path(temp_output)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Clean up
        output_path.unlink()

    finally:
        Path(temp_csv).unlink()


def test_pipeline_with_json_input() -> None:
    """Pipeline should process JSON input."""
    # Create temporary JSON file
    products = [
        {"title": "Chair", "sku": "C-1", "price": "100", "description": "A chair"},
        {"title": "Table", "sku": "T-1", "price": "200", "description": "A table"},
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(products, f)
        temp_json = f.name

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_output = f.name

        result = pipeline.process_products(
            filepath=temp_json,
            export_csv=True,
            output_csv_path=temp_output,
            upload_to_shopify=False,
        )

        assert result["success"] is True
        assert result["final_summary"]["total_input"] == 2

        Path(temp_output).unlink()

    finally:
        Path(temp_json).unlink()


def test_pipeline_handles_invalid_input() -> None:
    """Pipeline should handle invalid records gracefully."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "sku"])
        writer.writeheader()
        writer.writerow({"title": "Valid", "sku": "V-1"})
        writer.writerow({"title": "", "sku": "INVALID"})  # Missing title
        temp_csv = f.name

    try:
        result = pipeline.process_products(
            filepath=temp_csv,
            export_csv=False,
        )

        assert result["success"] is True
        assert result["final_summary"]["total_input"] == 2
        assert result["final_summary"]["successfully_processed"] == 1
        # Invalid record should be in validation results
        assert result["stages"]["validate"]["invalid_count"] == 1

    finally:
        Path(temp_csv).unlink()
