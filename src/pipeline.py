"""Main pipeline orchestrator for product data processing."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from src import ai_enhancer, exporter, ingest, logger as pipeline_logger, normalise, uploader, validate


def _build_review_output(
    raw_records: List[Dict[str, Any]],
    normalized_records: List[Dict[str, Any]],
    enhanced_by_index: Dict[int, Dict[str, Any]],
    invalid_indices: set[int],
    export_success: bool,
    export_csv: bool,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    handle_counts = validate.build_handle_counts(normalized_records)
    products: List[Dict[str, Any]] = []
    issue_counts: Dict[str, int] = {}
    status_counts = {
        "ready": 0,
        "needs_review": 0,
        "missing_fields": 0,
        "exported": 0,
    }

    for idx, (raw, normalized) in enumerate(zip(raw_records, normalized_records), start=1):
        issues = validate.generate_issues(normalized, handle_counts)
        base_status = validate.assign_status(issues)
        status = base_status
        if export_csv and export_success and base_status == "ready":
            status = "exported"

        shopify_row: Dict[str, Any] = {}
        if (idx - 1) not in invalid_indices:
            record_for_export = enhanced_by_index.get(idx - 1)
            if record_for_export:
                shopify_row = exporter.create_main_product_row(record_for_export)

        products.append({
            "product_id": f"row-{idx}",
            "row_index": idx,
            "status": status,
            "issues": issues,
            "raw_record": raw,
            "normalized_record": normalized,
            "shopify_row": shopify_row,
        })

        status_counts[status] = status_counts.get(status, 0) + 1
        for issue in issues:
            code = issue.get("code", "unknown")
            issue_counts[code] = issue_counts.get(code, 0) + 1

    summary = {
        "total": len(products),
        "ready": status_counts.get("ready", 0),
        "needs_review": status_counts.get("needs_review", 0),
        "missing_fields": status_counts.get("missing_fields", 0),
        "exported": status_counts.get("exported", 0),
        "issues": issue_counts,
    }

    return products, summary


def process_products(
    filepath: str,
    export_csv: bool = True,
    output_csv_path: str | None = None,
    upload_to_shopify: bool = False,
    ai_provider: str | None = None,
    job_id: str | None = None,
) -> Dict[str, Any]:
    """
    Complete pipeline: ingest → normalize → validate → enhance → export → upload.

    Args:
        filepath: Input CSV or JSON file path
        export_csv: Whether to generate Shopify CSV export
        output_csv_path: Path for output CSV (default: output.csv)
        upload_to_shopify: Whether to upload products to Shopify API
        ai_provider: AI provider ('openai', 'bedrock', or None)
        job_id: Optional job identifier for tracing (auto-generated if None)

    Returns:
        Dict with complete pipeline results including success/failures at each stage
    """
    if not output_csv_path:
        output_csv_path = "shopify_import.csv"

    # Initialize structured logger
    plog = pipeline_logger.PipelineLogger(job_id=job_id)
    plog.info("Pipeline started", input_file=filepath)

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
        "job_id": plog.job_id,
        "summary": {
            "total": 0,
            "ready": 0,
            "needs_review": 0,
            "missing_fields": 0,
            "exported": 0,
            "issues": {},
        },
        "products": [],
        "output": {
            "csv_key": None,
            "download_url": None,
        },
    }

    try:
        # Stage 1: Ingest
        with plog.step("ingest"):
            ingest_result = ingest.load_data(filepath)
            result["stages"]["ingest"] = ingest_result

            if not ingest_result["success"]:
                plog.error(f"Ingest failed: {ingest_result['error']}")
                result["final_summary"]["error"] = ingest_result["error"]
                return result

            records = ingest_result["records"]
            result["final_summary"]["total_input"] = len(records)
            plog.record_products_processed(len(records))

        # Stage 2: Normalize
        with plog.step("normalize"):
            normalize_result = normalise.normalize_records(records)
            result["stages"]["normalize"] = normalize_result

            if not normalize_result["success"]:
                plog.error(f"Normalize failed: {normalize_result['error']}")
                result["final_summary"]["error"] = normalize_result["error"]
                return result

            normalized_records = normalize_result["records"]

        # Stage 3: Validate
        with plog.step("validate"):
            validate_result = validate.validate_records(normalized_records)
            result["stages"]["validate"] = validate_result

            invalid_indices = {
                invalid_record["index"] for invalid_record in validate_result["invalid_records"]
            }

            if validate_result["valid_count"] == 0:
                plog.error("No valid records after validation")
                result["final_summary"]["error"] = "No valid records after validation"
                products, summary = _build_review_output(
                    records,
                    normalized_records,
                    {},
                    invalid_indices,
                    export_success=False,
                    export_csv=export_csv,
                )
                result["products"] = products
                result["summary"] = summary
                return result

            valid_records = validate_result["valid_records"]
            result["final_summary"]["successfully_processed"] = len(valid_records)
            plog.record_validation_metrics(
                validate_result["valid_count"],
                validate_result["invalid_count"],
            )

        # Stage 4: AI Enhancement (optional)
        if ai_provider:
            with plog.step("ai_enhance"):
                enhance_result = ai_enhancer.enhance_records(valid_records, ai_provider)
                result["stages"]["ai_enhance"] = enhance_result
                enhanced_records = enhance_result["records"]
        else:
            plog.debug("Skipping AI enhancement (no provider specified)")
            enhanced_records = valid_records

        valid_indices = [
            idx for idx in range(len(normalized_records)) if idx not in invalid_indices
        ]
        enhanced_by_index = {
            record_index: enhanced_records[pos]
            for pos, record_index in enumerate(valid_indices)
            if pos < len(enhanced_records)
        }

        # Stage 5: Export to CSV (optional)
        export_success = False
        if export_csv:
            with plog.step("export"):
                export_result = exporter.export_to_csv(enhanced_records, output_csv_path)
                result["stages"]["export"] = export_result

                if export_result["success"]:
                    result["final_summary"]["exported"] = True
                    plog.info(f"Exported to {output_csv_path}")
                    result["output"]["csv_key"] = export_result["filepath"]
                    export_success = True
                else:
                    plog.error(f"Export failed: {export_result['error']}")
                    result["final_summary"]["error"] = export_result["error"]
                    products, summary = _build_review_output(
                        records,
                        normalized_records,
                        enhanced_by_index,
                        invalid_indices,
                        export_success=False,
                        export_csv=export_csv,
                    )
                    result["products"] = products
                    result["summary"] = summary
                    return result

        # Stage 6: Upload to Shopify (optional)
        if upload_to_shopify:
            with plog.step("upload"):
                upload_result = uploader.upload_products(enhanced_records)
                result["stages"]["upload"] = upload_result

                if upload_result["success"]:
                    result["final_summary"]["uploaded"] = True
                    plog.info("Successfully uploaded to Shopify")
                else:
                    plog.warning(f"Upload to Shopify failed: {upload_result['error']}")
                    result["final_summary"]["error"] = upload_result["error"]

        products, summary = _build_review_output(
            records,
            normalized_records,
            enhanced_by_index,
            invalid_indices,
            export_success=export_success,
            export_csv=export_csv,
        )
        result["products"] = products
        result["summary"] = summary

        # Mark overall success
        result["success"] = True
        result["logging"] = plog.log_pipeline_summary()
        plog.info("Pipeline completed successfully", status="success")
        return result

    except Exception as e:
        plog.error(f"Pipeline execution failed: {str(e)}")
        result["final_summary"]["error"] = str(e)
        result["logging"] = plog.log_pipeline_summary()
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
