"""
Tests for confidence.py -- checking the weighted formula behaves
sensibly (clean, complete, evidenced records score high; incomplete
or unsupported records score meaningfully lower).
"""

from app.confidence import calculate_confidence
from app.schemas import empty_record
from app.validator import validate_schema_and_types, check_evidence


def test_perfect_record_scores_high():
    ocr_text = (
        "Owner Name: Ram Kumar\n"
        "Khasra No: 142/2\n"
        "Area: 1.25 hectare\n"
        "Village: Rampur\n"
        "Tehsil: Sadar\n"
        "District: Lucknow\n"
        "Land Use: Agricultural\n"
    )
    record = empty_record()
    record.update({
        "owner_name": "Ram Kumar",
        "khasra_number": "142/2",
        "area": 1.25,
        "area_unit": "hectare",
        "village": "Rampur",
        "tehsil": "Sadar",
        "district": "Lucknow",
        "land_use": "Agricultural",
    })

    validation = validate_schema_and_types(record)
    evidence = check_evidence(record, ocr_text)
    confidence = calculate_confidence(record, validation, evidence, ocr_metadata={"ocr_confidence": 0.95})

    assert confidence["final_confidence"] >= 90


def test_empty_record_scores_low():
    record = empty_record()
    validation = validate_schema_and_types(record)
    evidence = check_evidence(record, "")
    confidence = calculate_confidence(record, validation, evidence, ocr_metadata=None)

    # An entirely empty record should never accidentally look
    # "confident" -- completeness is 0, which should pull the score
    # down substantially.
    assert confidence["final_confidence"] < 90


def test_unsupported_fields_reduce_confidence_more_than_missing_fields():
    ocr_text = "Owner Name: Ram Kumar\n"

    # Case A: fields are simply missing (null) -- honest gap.
    record_missing = empty_record()
    record_missing["owner_name"] = "Ram Kumar"
    validation_missing = validate_schema_and_types(record_missing)
    evidence_missing = check_evidence(record_missing, ocr_text)
    confidence_missing = calculate_confidence(record_missing, validation_missing, evidence_missing)

    # Case B: same completeness, but the extra fields are hallucinated
    # (not present in OCR at all).
    record_hallucinated = empty_record()
    record_hallucinated.update({
        "owner_name": "Ram Kumar",
        "district": "Lucknow",  # not present in ocr_text
        "tehsil": "Sadar",       # not present in ocr_text
    })
    validation_hallucinated = validate_schema_and_types(record_hallucinated)
    evidence_hallucinated = check_evidence(record_hallucinated, ocr_text)
    confidence_hallucinated = calculate_confidence(record_hallucinated, validation_hallucinated, evidence_hallucinated)

    assert confidence_hallucinated["final_confidence"] < confidence_missing["final_confidence"]


def test_breakdown_contains_all_components():
    record = empty_record()
    validation = validate_schema_and_types(record)
    evidence = check_evidence(record, "")
    confidence = calculate_confidence(record, validation, evidence)

    breakdown = confidence["breakdown"]
    for key in ["ocr_quality_score", "completeness_score", "validation_score", "evidence_score", "ambiguity_penalty"]:
        assert key in breakdown
