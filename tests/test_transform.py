from src.pipeline.transform import normalize_record, process_records, validate_record


def test_normalize_record_trims_strings() -> None:
    rec = normalize_record({"title": "  Chair  ", "sku": " SKU-1 "})
    assert rec["title"] == "Chair"
    assert rec["sku"] == "SKU-1"


def test_validate_record_requires_title_and_sku() -> None:
    errs = validate_record({"title": "", "sku": ""})
    assert "missing_required_field:title" in errs
    assert "missing_required_field:sku" in errs


def test_process_records_counts_processed_and_warnings() -> None:
    result = process_records(
        [
            {"title": "Table", "sku": "T-1"},
            {"title": "", "sku": "BAD"},
        ]
    )
    assert result["processed_count"] == 1
    assert result["warning_count"] == 1
