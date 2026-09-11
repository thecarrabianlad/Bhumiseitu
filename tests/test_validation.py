"""
Test 4, 5, 6, 7, 8 from the requirements:
    - Missing fields
    - Bad OCR
    - Hallucination prevention
    - Invalid area
    - Unrelated numbers (dates/pages/phone numbers)
"""

from app.extractor import extract_land_record
from app.llm_client import MockLLMClient, LLMClient
from app.validator import validate_schema_and_types, check_evidence
from app.schemas import empty_record


def test_missing_fields_return_null_not_invented():
    ocr_text = (
        "Owner Name: Ram Kumar\n"
        "Khasra No: 142/2\n"
        "Area: 1.25 hectare\n"
        "Village: Rampur\n"
        # No Tehsil, District, or Land Use present at all.
    )

    result = extract_land_record(ocr_text, llm_client=MockLLMClient())
    data = result["extracted_data"]

    assert data["tehsil"] is None
    assert data["district"] is None
    assert data["land_use"] is None
    # And critically: district must NOT be guessed as "Lucknow" or
    # anything else just because Rampur/Lucknow is a common pairing.
    assert data["district"] != "Lucknow"


def test_bad_ocr_extracts_reasonable_fields_but_flags_unit_problem():
    ocr_text = (
        "0wner Nane: Rarn Kurnar\n"
        "Khasra N0: 14Z/2\n"
        "Arca: 1.25 hectar\n"
        "Vilage: Rampur\n"
    )

    result = extract_land_record(ocr_text, llm_client=MockLLMClient())
    data = result["extracted_data"]

    # Reasonable extraction still happens where evidence is clear.
    assert data["owner_name"] == "Rarn Kurnar"
    assert data["village"] == "Rampur"
    # "hectar" is a misspelling of a valid unit; our validator does not
    # blindly "fix" it, so it correctly fails validation and gets
    # nulled out. This is a deliberate design choice: safer to lose a
    # bit of completeness than to silently pretend a misspelled unit
    # is fine.
    assert data["area_unit"] is None
    # Confidence should not be perfect on noisy OCR.
    assert result["confidence"] < 100


def test_hallucination_prevention_unsupported_value_is_nulled():
    """Simulates an LLM that hallucinates a district that is NOT
    present anywhere in the OCR text. P3 must detect this and null it
    out rather than trusting the LLM."""

    ocr_text = "Owner: Ram Kumar\nVillage: Rampur\n"

    class HallucinatingClient(LLMClient):
        def extract_raw(self, ocr_text: str) -> dict:
            record = empty_record()
            record["owner_name"] = "Ram Kumar"
            record["village"] = "Rampur"
            record["district"] = "Lucknow"  # NOT present in ocr_text at all
            return record

    result = extract_land_record(ocr_text, llm_client=HallucinatingClient())
    data = result["extracted_data"]

    assert data["owner_name"] == "Ram Kumar"
    assert data["village"] == "Rampur"
    # The hallucinated, unsupported district must be nulled out.
    assert data["district"] is None
    assert "district" in result["diagnostics"]["unsupported_fields"]
    # Confidence must be meaningfully reduced by the hallucination.
    assert result["confidence"] < 90


def test_evidence_checker_directly_flags_unsupported_value():
    ocr_text = "Owner: Ram Kumar\nVillage: Rampur\n"
    candidate = empty_record()
    candidate["owner_name"] = "Ram Kumar"
    candidate["district"] = "Lucknow"

    evidence = check_evidence(candidate, ocr_text)
    assert evidence["supported"]["owner_name"] is True
    assert evidence["supported"]["district"] is False
    assert "district" in evidence["unsupported_fields"]


def test_invalid_area_non_numeric_becomes_null():
    ocr_text = "Owner Name: Ram Kumar\nArea: abc\n"
    result = extract_land_record(ocr_text, llm_client=MockLLMClient())
    assert result["extracted_data"]["area"] is None


def test_invalid_area_negative_becomes_null():
    ocr_text = "Owner Name: Ram Kumar\nArea: -5 hectare\n"
    result = extract_land_record(ocr_text, llm_client=MockLLMClient())
    assert result["extracted_data"]["area"] is None


def test_validator_directly_rejects_negative_area():
    record = empty_record()
    record["area"] = -5.0
    validation = validate_schema_and_types(record)
    assert validation["field_results"]["area"] is False
    assert any("negative" in e for e in validation["errors"])


def test_unrelated_numbers_are_not_mistaken_for_khasra_or_area():
    ocr_text = (
        "Owner Name: Ram Kumar\n"
        "Date: 12/04/2025\n"
        "Page: 4\n"
        "Phone: 9876543210\n"
    )
    result = extract_land_record(ocr_text, llm_client=MockLLMClient())
    data = result["extracted_data"]

    assert data["khasra_number"] is None
    assert data["area"] is None
