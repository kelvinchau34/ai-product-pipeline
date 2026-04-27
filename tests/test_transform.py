"""Tests for data transformation pipeline modules."""

from src import ai_enhancer, exporter, normalise, validate


def test_normalize_product_cleans_strings() -> None:
    """Normalize module should trim whitespace from fields."""
    product = {"title": "  Chair  ", "sku": " SKU-1 ", "description": "  A chair  "}
    normalized = normalise.normalize_product(product)
    assert normalized["title"] == "Chair"
    assert normalized["sku"] == "SKU-1"
    assert normalized["description"] == "A chair"


def test_validate_product_requires_title_and_sku() -> None:
    """Validation should fail if title or sku missing."""
    product = {"title": "", "sku": "", "description": "No title or sku"}
    errors = validate.validate_product(product)
    assert "missing_required_field:title" in errors
    assert "missing_required_field:sku" in errors


def test_validate_product_checks_valid_price() -> None:
    """Validation should reject invalid prices."""
    product = {"title": "Chair", "sku": "SKU-1", "price": "not_a_number"}
    errors = validate.validate_product(product)
    assert any("invalid_price" in err for err in errors)


def test_validate_records_separates_valid_invalid() -> None:
    """Validation should categorize records as valid or invalid."""
    records = [
        {"title": "Chair", "sku": "SKU-1"},
        {"title": "", "sku": "SKU-2"},  # Invalid: no title
    ]
    result = validate.validate_records(records)
    assert result["valid_count"] == 1
    assert result["invalid_count"] == 1
    assert len(result["valid_records"]) == 1
    assert len(result["invalid_records"]) == 1


def test_exporter_create_handle_formats_properly() -> None:
    """Exporter should format handles correctly."""
    assert exporter.create_handle("Sample Chair") == "sample-chair"
    assert exporter.create_handle("Bar-Stool!@#") == "bar-stool"
    assert exporter.create_handle("  Multi   Space  ") == "multi-space"


def test_exporter_detect_product_type_recognizes_types() -> None:
    """Exporter should detect product types from title/description."""
    assert exporter.detect_product_type("Dining Chair", "A wooden chair") == "dining chair"
    assert exporter.detect_product_type("Sofa Bed", "Comfortable seating") == "sofa"
    assert exporter.detect_product_type("Random Item", "No keywords here") == "furniture"


def test_ai_enhancer_skips_when_no_provider() -> None:
    """AI enhancer should skip if no provider specified."""
    records = [{"title": "Chair", "sku": "SKU-1"}]
    result = ai_enhancer.enhance_records(records, provider=None)
    assert result["success"] is True
    assert result["enhanced_count"] == 0
    assert result["skipped_count"] == 1


def test_exporter_body_html_uses_reference_template_sections() -> None:
    """Exporter should produce reference template markup with mapped section content."""
    product = {
        "title": "Wallie wall drawer",
        "description": "Short fallback description",
        "description_long": "Long product story",
        "designs_available": "Available in oak and walnut",
        "fabric_colour": "Walnut",
        "height_mm": "100",
        "width_mm": "225",
        "depth_mm": "300",
        "weight_display": "3,00",
        "certifications": "FSC, Prop 65",
        "care_guide_url": "https://example.com/care.pdf",
        "assembly_instruction_url": "https://example.com/assembly.pdf",
        "sku": "WALLIE-1",
        "price": "179.00",
        "grams": 3000,
        "weight_unit": "g",
        "barcode": "123",
        "images": [],
        "image_alt_text": "Wallie",
    }

    row = exporter.create_main_product_row(product)
    body_html = row["Body (HTML)"]

    assert "<style>" in body_html
    assert "<script>" in body_html
    assert "<button class=\"collapsible\">Details</button>" in body_html
    assert "Long product story" in body_html
    assert "Available in oak and walnut" in body_html
    assert "Walnut" in body_html
    assert "Height: 10cm" in body_html
    assert "Width: 22.5cm" in body_html
    assert "Depth: 30cm" in body_html
    assert "Weight: 3kg" in body_html
    assert "<button class=\"collapsible\">Certifications</button>" in body_html
    assert "FSC" in body_html
    assert "Prop 65" in body_html
    assert "<button class=\"collapsible\">Files</button>" in body_html
    assert "https://example.com/care.pdf" in body_html
    assert "https://example.com/assembly.pdf" in body_html


def test_exporter_body_html_omits_optional_empty_sections() -> None:
    """Exporter should omit Certifications and Files blocks when source data is missing."""
    product = {
        "title": "Simple Product",
        "description": "Simple description",
        "designs_available": "",
        "fabric_colour": "",
        "height_mm": "",
        "width_mm": "",
        "depth_mm": "",
        "weight_display": "",
        "certifications": "",
        "care_guide_url": "",
        "assembly_instruction_url": "",
        "sku": "SIMPLE-1",
        "price": "10",
        "grams": 0,
        "weight_unit": "g",
        "barcode": "",
        "images": [],
        "image_alt_text": "Simple Product",
    }

    row = exporter.create_main_product_row(product)
    body_html = row["Body (HTML)"]

    assert "<button class=\"collapsible\">Certifications</button>" not in body_html
    assert "<button class=\"collapsible\">Files</button>" not in body_html

