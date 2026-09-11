"""
Test 1, 2, 3 from the requirements:
    - Clean English OCR
    - Hindi OCR
    - Mixed Hindi-English OCR
"""

from app.extractor import extract_land_record
from app.llm_client import MockLLMClient


def test_clean_english_ocr():
    ocr_text = (
        "Owner Name: Ram Kumar\n"
        "Khasra No: 142/2\n"
        "Area: 1.25 hectare\n"
        "Village: Rampur\n"
        "Tehsil: Sadar\n"
        "District: Lucknow\n"
        "Land Use: Agricultural\n"
    )

    result = extract_land_record(ocr_text, llm_client=MockLLMClient())
    data = result["extracted_data"]

    assert data["owner_name"] == "Ram Kumar"
    assert data["khasra_number"] == "142/2"
    assert data["area"] == 1.25
    assert data["area_unit"] == "hectare"
    assert data["village"] == "Rampur"
    assert data["tehsil"] == "Sadar"
    assert data["district"] == "Lucknow"
    assert data["land_use"] == "Agricultural"
    assert result["confidence"] >= 90
    assert result["route"] == "AUTO_SAVE"


def test_hindi_ocr():
    ocr_text = (
        "खातेदार: सुनीता देवी\n"
        "खसरा नंबर: 88/1\n"
        "क्षेत्रफल: 2 बीघा\n"
        "ग्राम: नरसिंहपुर\n"
        "तहसील: बिलासपुर\n"
        "जिला: रायपुर\n"
        "भू-उपयोग: कृषि\n"
    )

    result = extract_land_record(ocr_text, llm_client=MockLLMClient())
    data = result["extracted_data"]

    assert data["owner_name"] == "सुनीता देवी"
    assert data["khasra_number"] == "88/1"
    assert data["area"] == 2
    assert data["area_unit"] == "bigha"
    assert data["village"] == "नरसिंहपुर"
    assert data["tehsil"] == "बिलासपुर"
    assert data["district"] == "रायपुर"
    assert data["land_use"] == "कृषि"


def test_mixed_hindi_english_ocr():
    ocr_text = (
        "Owner Name: Suresh Yadav\n"
        "खसरा नंबर: 210/3\n"
        "Area: 0.75 acre\n"
        "ग्राम: Bhagwanpur\n"
        "Tehsil: Sadar\n"
        "जिला: Kanpur\n"
        "Land Use: Residential\n"
    )

    result = extract_land_record(ocr_text, llm_client=MockLLMClient())
    data = result["extracted_data"]

    assert data["owner_name"] == "Suresh Yadav"
    assert data["khasra_number"] == "210/3"
    assert data["area"] == 0.75
    assert data["area_unit"] == "acre"
    assert data["village"] == "Bhagwanpur"
    assert data["tehsil"] == "Sadar"
    assert data["district"] == "Kanpur"
    assert data["land_use"] == "Residential"
