"""AWS Lambda handler for product pipeline."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from src import pipeline


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
    try:
        # Extract parameters from event
        input_file = event.get("input_file", "")
        output_csv = event.get("output_csv", "shopify_import.csv")
        export_csv = event.get("export_csv", True)
        upload_shopify = event.get("upload_shopify", False)
        ai_provider = event.get("ai_provider")

        if not input_file:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "input_file parameter required",
                }),
            }

        # Run pipeline
        result = pipeline.process_products(
            filepath=input_file,
            export_csv=export_csv,
            output_csv_path=output_csv,
            upload_to_shopify=upload_shopify,
            ai_provider=ai_provider,
        )

        return {
            "statusCode": 200 if result["success"] else 400,
            "body": json.dumps(result),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Pipeline failed: {str(e)}",
            }),
        }


if __name__ == "__main__":
    # Local testing
    test_event = {
        "input_file": "input_examples/sample_input.csv",
        "output_csv": "output/test_output.csv",
        "export_csv": True,
        "upload_shopify": False,
    }
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))

