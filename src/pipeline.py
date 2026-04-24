"""Main pipeline orchestrator for product data processing."""

from __future__ import annotations

from typing import Any, Dict, List

from src import ai_enhancer, exporter, ingest, normalise, uploader, validate


def process_products(
    filepath: str,
    export_csv: bool = True,
    output_csv_path: str | None = None,
    upload_to_shopify: bool = False,
    ai_provider: str | None = None,
) -> Dict[str, Any]:
    """
    Complete pipeline: ingest → normalize → validate → enhance → export → upload.

    Args:
        filepath: Input CSV or JSON file path
        export_csv: Whether to generate Shopify CSV export
        output_csv_path: Path for output CSV (default: output.csv)
        upload_to_shopify: Whether to upload products to Shopify API
        ai_provider: AI provider ('openai', 'bedrock', or None)

    Returns:
        Dict with complete pipeline results including success/failures at each stage
    """
    if not output_csv_path:
        output_csv_path = "shopify_import.csv"

    result = {
        "success": False,
        "stages": {},
        "final_summary": {
            "input_file": filepath,
            "total_input": 0,
            "successfully_processed": 0,
            "exported": False,
            "uploaded": False,
            "error": None,
        },
    }

    # Stage 1: Ingest
    ingest_result = ingest.load_data(filepath)
    result["stages"]["ingest"] = ingest_result

    if not ingest_result["success"]:
        result["final_summary"]["error"] = ingest_result["error"]
        return result

    records = ingest_result["records"]
    result["final_summary"]["total_input"] = len(records)

    # Stage 2: Normalize
    normalize_result = normalise.normalize_records(records)
    result["stages"]["normalize"] = normalize_result

    if not normalize_result["success"]:
        result["final_summary"]["error"] = normalize_result["error"]
        return result

    normalized_records = normalize_result["records"]

    # Stage 3: Validate
    validate_result = validate.validate_records(normalized_records)
    result["stages"]["validate"] = validate_result

    if validate_result["valid_count"] == 0:
        result["final_summary"]["error"] = "No valid records after validation"
        return result

    valid_records = validate_result["valid_records"]
    result["final_summary"]["successfully_processed"] = len(valid_records)

    # Stage 4: AI Enhancement (optional)
    enhance_result = ai_enhancer.enhance_records(valid_records, ai_provider)
    result["stages"]["ai_enhance"] = enhance_result
    enhanced_records = enhance_result["records"]

    # Stage 5: Export to CSV (optional)
    if export_csv:
        export_result = exporter.export_to_csv(enhanced_records, output_csv_path)
        result["stages"]["export"] = export_result

        if export_result["success"]:
            result["final_summary"]["exported"] = True
        else:
            result["final_summary"]["error"] = export_result["error"]
            return result

    # Stage 6: Upload to Shopify (optional)
    if upload_to_shopify:
        upload_result = uploader.upload_products(enhanced_records)
        result["stages"]["upload"] = upload_result

        if upload_result["success"]:
            result["final_summary"]["uploaded"] = True
        else:
            result["final_summary"]["error"] = upload_result["error"]

    # Mark overall success
    result["success"] = True
    return result


def process_with_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run pipeline with configuration dict.

    Args:
        config: Dict with keys:
            - input_file (str): Input CSV/JSON path
            - output_csv (str, optional): Output CSV path
            - export_csv (bool, optional): Generate CSV
            - upload_shopify (bool, optional): Upload to Shopify
            - ai_provider (str, optional): AI provider name

    Returns:
        Pipeline results dict
    """
    return process_products(
        filepath=config.get("input_file", ""),
        export_csv=config.get("export_csv", True),
        output_csv_path=config.get("output_csv"),
        upload_to_shopify=config.get("upload_shopify", False),
        ai_provider=config.get("ai_provider"),
    )
