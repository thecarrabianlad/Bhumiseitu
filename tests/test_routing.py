"""
Test 9 and 10 from the requirements:
    - Confidence >= 90 routes to AUTO_SAVE
    - Confidence < 90 routes to CLERK_REVIEW
"""

from app.router import decide_route, ROUTE_AUTO_SAVE, ROUTE_CLERK_REVIEW
from app.llm_client import MockLLMClient, LLMClient
from app.extractor import extract_land_record
from app.schemas import empty_record


def test_decide_route_boundary_values():
    assert decide_route(90.0) == ROUTE_AUTO_SAVE
    assert decide_route(90.1) == ROUTE_AUTO_SAVE
    assert decide_route(100.0) == ROUTE_AUTO_SAVE
    assert decide_route(89.9) == ROUTE_CLERK_REVIEW
    assert decide_route(0.0) == ROUTE_CLERK_REVIEW


def test_clean_complete_ocr_routes_to_auto_save():
    ocr_text = (
        "Owner Name: Ram Kumar\n"
        "Khasra No: 142/2\n"
        "Area: 1.25 hectare\n"
        "Village: Rampur\n"
        "Tehsil: Sadar\n"
        "District: Lucknow\n"
        "Land Use: Agricultural\n"
    )
    result = extract_land_record(
        ocr_text,
        ocr_metadata={"ocr_confidence": 0.95},
        llm_client=MockLLMClient(),
    )
    assert result["route"] == ROUTE_AUTO_SAVE
    assert result["confidence"] >= 90


def test_sparse_ocr_routes_to_clerk_review():
    ocr_text = "Owner Name: Ram Kumar\n"
    result = extract_land_record(ocr_text, llm_client=MockLLMClient())
    assert result["route"] == ROUTE_CLERK_REVIEW
    assert result["confidence"] < 90


def test_hallucinated_record_routes_to_clerk_review():
    ocr_text = "Owner: Ram Kumar\nVillage: Rampur\n"

    class HallucinatingClient(LLMClient):
        def extract_raw(self, ocr_text: str) -> dict:
            record = empty_record()
            record["owner_name"] = "Ram Kumar"
            record["village"] = "Rampur"
            record["khasra_number"] = "999/9"  # not present -> hallucinated
            record["district"] = "Lucknow"     # not present -> hallucinated
            record["tehsil"] = "Sadar"         # not present -> hallucinated
            record["land_use"] = "Agricultural"  # not present -> hallucinated
            return record

    result = extract_land_record(ocr_text, llm_client=HallucinatingClient())
    assert result["route"] == ROUTE_CLERK_REVIEW
    assert result["confidence"] < 90
