"""AWS Lambda handler for product pipeline."""

from __future__ import annotations

import base64
import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict

import boto3

from src import logger as pipeline_logger, pipeline


def _parse_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse direct Lambda events and API Gateway proxy events."""
    body = event.get("body")
    if event.get("isBase64Encoded") and isinstance(body, str):
        try:
            body = base64.b64decode(body).decode("utf-8")
        except Exception:
            pass

    if isinstance(body, str):
        try:
            parsed_body = json.loads(body)
            if isinstance(parsed_body, dict):
                return parsed_body
        except json.JSONDecodeError:
            pass
    if isinstance(body, dict):
        return body
    return event


def _is_s3_uri(value: str) -> bool:
    return value.startswith("s3://")


def _parse_s3_uri(uri: str) -> tuple[str, str]:
    stripped = uri.replace("s3://", "", 1)
    bucket, _, key = stripped.partition("/")
    return bucket, key


def _download_s3_to_tmp(s3_client: Any, bucket: str, key: str) -> str:
    filename = Path(key).name or "input.csv"
    local_path = f"/tmp/{filename}"
    s3_client.download_file(bucket, key, local_path)
    return local_path


def _upload_file_to_s3(s3_client: Any, local_path: str, bucket: str, key: str) -> str:
    s3_client.upload_file(local_path, bucket, key)
    return f"s3://{bucket}/{key}"


def _create_presigned_download_url(s3_client: Any, bucket: str, key: str, expires_in: int = 3600) -> str:
    return s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def _write_text_to_tmp(file_name: str, content: str) -> str:
    safe_name = Path(file_name).name or "input.csv"
    local_path = f"/tmp/{safe_name}"
    with open(local_path, "w", encoding="utf-8") as file_handle:
        file_handle.write(content)
    return local_path


def _compact_result_for_response(result: Dict[str, Any]) -> Dict[str, Any]:
    """Return a lightweight response body for API clients."""
    compact = {
        "success": result.get("success", False),
        "final_summary": result.get("final_summary", {}),
        "stages": {},
    }

    for stage_name, stage_data in result.get("stages", {}).items():
        if not isinstance(stage_data, dict):
            compact["stages"][stage_name] = stage_data
            continue

        compact_stage = {k: v for k, v in stage_data.items() if k not in {"records", "valid_records", "invalid_records", "results"}}
        compact["stages"][stage_name] = compact_stage

    if "output_s3_uri" in result:
        compact["output_s3_uri"] = result["output_s3_uri"]
    if "output_key" in result:
        compact["output_key"] = result["output_key"]

    return compact


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for product data processing pipeline.

    Expected event structure:
    {
        "input_file": "s3://bucket/path/input.csv",
        "output_csv": "s3://bucket/path/output.csv",
        "export_csv": true,
        "upload_shopify": false,
        "ai_provider": null
    }

    Returns:
        Lambda response with statusCode and body containing pipeline results
    """
    # Initialize structured logger with unique job_id
    job_id = str(uuid.uuid4())
    plog = pipeline_logger.PipelineLogger(job_id=job_id)
    plog.info("Lambda handler invoked", context_function_name=context.function_name if context else None)

    try:
        payload = _parse_event(event)
        plog.debug("Event parsed successfully", payload_keys=list(payload.keys()))

        # Environment defaults
        default_bucket = os.getenv("PIPELINE_BUCKET", "")
        input_prefix = os.getenv("INPUT_PREFIX", "input")
        output_prefix = os.getenv("OUTPUT_PREFIX", "output")
        default_upload_shopify = os.getenv("DEFAULT_UPLOAD_SHOPIFY", "false").lower() == "true"
        default_ai_provider = os.getenv("DEFAULT_AI_PROVIDER")

        # Extract parameters from event payload
        bucket = payload.get("bucket") or default_bucket
        input_file = payload.get("input_file", "")
        input_key = payload.get("input_key", "")
        file_name = payload.get("file_name", "")
        file_content = payload.get("file_content", "")
        output_csv = payload.get("output_csv", "shopify_import.csv")
        output_key = payload.get("output_key", "")
        export_csv = payload.get("export_csv", True)
        upload_shopify = payload.get("upload_shopify", default_upload_shopify)
        dry_run = payload.get("dry_run", False)
        ai_provider = payload.get("ai_provider", default_ai_provider)

        if dry_run:
            upload_shopify = False

        s3_client = boto3.client("s3")

        # Resolve input path: direct file content, s3 uri, input_key+bucket, or local filepath
        if file_content and file_name:
            input_file = _write_text_to_tmp(file_name, file_content)

        if input_key and not input_file:
            if not bucket:
                plog.error("bucket is required when input_key is provided")
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "job_id": job_id,
                        "error": "bucket is required when input_key is provided",
                    }),
                }
            input_file = f"s3://{bucket}/{input_key}"

        # Fallback to default input prefix when only a filename is provided
        if input_file and not _is_s3_uri(input_file) and bucket and not Path(input_file).exists():
            input_file = f"s3://{bucket}/{input_prefix.strip('/')}/{input_file.lstrip('/')}"

        if not input_file:
            plog.error("input_file or input_key parameter required")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "job_id": job_id,
                    "error": "input_file or input_key parameter required",
                }),
            }

        local_input_file = input_file
        if _is_s3_uri(input_file):
            in_bucket, in_key = _parse_s3_uri(input_file)
            local_input_file = _download_s3_to_tmp(s3_client, in_bucket, in_key)

        local_output_csv = output_csv
        if export_csv and (_is_s3_uri(output_csv) or output_key or bucket):
            local_output_csv = "/tmp/shopify_import.csv"

        # Run pipeline
        result = pipeline.process_products(
            filepath=local_input_file,
            export_csv=export_csv,
            output_csv_path=local_output_csv,
            upload_to_shopify=upload_shopify,
            ai_provider=ai_provider,
            job_id=job_id,
        )

        output_s3_uri = None
        download_url = None
        if result.get("success") and export_csv and bucket:
            resolved_output_key = output_key
            if not resolved_output_key:
                output_name = Path(output_csv).name if output_csv else "shopify_import.csv"
                resolved_output_key = f"{output_prefix.strip('/')}/{output_name}"

            output_s3_uri = _upload_file_to_s3(
                s3_client=s3_client,
                local_path=local_output_csv,
                bucket=bucket,
                key=resolved_output_key,
            )
            download_url = _create_presigned_download_url(s3_client, bucket, resolved_output_key)
            result["output_s3_uri"] = output_s3_uri
            result["output_key"] = resolved_output_key
            result["download_url"] = download_url
            plog.info(f"Exported to S3: {output_s3_uri}")

        response_body = {
            "job_id": job_id,
            "request": {
                "bucket": bucket,
                "file_name": file_name,
                "input_file": input_file,
                "output_csv": output_csv,
                "output_s3_uri": output_s3_uri,
                "download_url": download_url,
            },
            "result": _compact_result_for_response(result),
        }

        # Add logging summary if available
        if "logging" in result:
            response_body["logging"] = result["logging"]

        plog.info("Lambda handler completed successfully", status="success")
        return {
            "statusCode": 200 if result["success"] else 400,
            "body": json.dumps(response_body),
        }

    except Exception as e:
        plog.error(f"Lambda handler failed: {str(e)}", status="failed")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "job_id": job_id,
                "error": f"Pipeline failed: {str(e)}",
            }),
        }


if __name__ == "__main__":
    # Local testing
    test_event = {
        "input_file": "input_examples/sample-input.csv",
        "output_csv": "output/test_output.csv",
        "export_csv": True,
        "upload_shopify": False,
    }
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))

