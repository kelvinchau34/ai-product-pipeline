from __future__ import annotations

import json
from typing import Any, Dict

from src.pipeline.transform import process_records


def handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    records = event.get("records", [])
    result = process_records(records)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(result),
    }


if __name__ == "__main__":
    sample_event = {
        "records": [
            {"title": "Sample Chair", "sku": "CHAIR-001", "price": "129.99"},
            {"title": "", "sku": "BAD-001"},
        ]
    }
    print(handler(sample_event, None))
