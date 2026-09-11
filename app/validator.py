"""
validator.py
------------
This file checks the LLM's candidate JSON using plain, predictable
Python code -- NOT another AI call. This is called "deterministic
validation": the same input always produces exactly the same output,
because it's just ordinary if/else logic and regular expressions,
with no randomness and no "creativity" involved.

Why do we need this if the LLM already extracted the data?
    Because we must never blindly trust the LLM. It might return the
    wrong data type, an empty string instead of null, a khasra number
    that isn't really a khasra number, a negative area, etc. This file
    is our independent double-check.

This file does two separate jobs:
    1. `validate_schema_and_types()` -- structural checks (right
       keys, right types, sensible values).
    2. `check_evidence()` -- hallucination prevention: for each
       non-null field, confirm the value (or something very close to
       it) actually appears in the original OCR text. If it doesn't,
       we don't trust it.
"""

import re
from typing import Optional

from app.schemas import REQUIRED_FIELDS, KNOWN_AREA_UNITS


# ---------------------------------------------------------------------------
# 1. Structural / type validation
# ---------------------------------------------------------------------------

def validate_schema_and_types(record: dict) -> dict:
    """Check that `record` has exactly the right keys and that each
    value is a sensible type/format.

    Returns a dict:
        {
            "field_results": {field_name: True/False, ...},
            "errors": [list of human-readable problem descriptions],
        }
    `field_results[field] = True` means "this field passed validation"
    (this includes the common, valid case of the field being null).
    """
    field_results = {}
    errors = []

    # (a) No unexpected fields, no missing fields.
    record_keys = set(record.keys())
    expected_keys = set(REQUIRED_FIELDS)
    missing = expected_keys - record_keys
    extra = record_keys - expected_keys
    if missing:
        errors.append(f"Missing required fields: {sorted(missing)}")
    if extra:
        errors.append(f"Unexpected extra fields: {sorted(extra)}")

    # (b) Per-field checks. Any field not present at all is treated as
    # failing that field's check.
    field_results["owner_name"] = _validate_owner_name(record.get("owner_name"), errors)
    field_results["khasra_number"] = _validate_khasra(record.get("khasra_number"), errors)
    field_results["area"] = _validate_area(record.get("area"), errors)
    field_results["area_unit"] = _validate_area_unit(record.get("area_unit"), errors)
    field_results["village"] = _validate_place_string(record.get("village"), "village", errors)
    field_results["tehsil"] = _validate_place_string(record.get("tehsil"), "tehsil", errors)
    field_results["district"] = _validate_place_string(record.get("district"), "district", errors)
    field_results["land_use"] = _validate_land_use(record.get("land_use"), errors)

    return {"field_results": field_results, "errors": errors}


def _validate_owner_name(value, errors) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        errors.append("owner_name must be a string or null")
        return False
    stripped = value.strip()
    if stripped == "":
        errors.append("owner_name is an empty string, should be null instead")
        return False
    # Reject obvious "garbage": pure digits/punctuation, or the label
    # itself echoed back (a common LLM mistake).
    if re.fullmatch(r"[\d\W]+", stripped):
        errors.append("owner_name looks like garbage (no letters)")
        return False
    if stripped.lower() in {"owner", "owner name", "name", "नाम", "खातेदार"}:
        errors.append("owner_name repeats the field label instead of a real value")
        return False
    return True


def _validate_khasra(value, errors) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        errors.append("khasra_number must be a string or null")
        return False
    stripped = value.strip()
    # Accept things like 142, 142/2, 45-A, 123/1
    if not re.fullmatch(r"[A-Za-z0-9]+([/\-][A-Za-z0-9]+)*", stripped):
        errors.append(f"khasra_number '{value}' does not match expected format")
        return False
    return True


def _validate_area(value, errors) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):  # bool is a subclass of int -- exclude it
        errors.append("area must be numeric, not boolean")
        return False
    if not isinstance(value, (int, float)):
        errors.append("area must be numeric or null")
        return False
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        errors.append("area is not a finite number")
        return False
    if numeric != numeric or numeric in (float("inf"), float("-inf")):  # NaN / inf check
        errors.append("area must be a finite number")
        return False
    if numeric < 0:
        errors.append("area cannot be negative")
        return False
    return True


def _validate_area_unit(value, errors) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        errors.append("area_unit must be a string or null")
        return False
    normalised = KNOWN_AREA_UNITS.get(value.lower(), KNOWN_AREA_UNITS.get(value))
    if normalised is None:
        errors.append(f"area_unit '{value}' is not a recognised unit")
        return False
    return True


def _validate_place_string(value, field_name, errors) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        errors.append(f"{field_name} must be a string or null")
        return False
    stripped = value.strip()
    if stripped == "" or re.fullmatch(r"[\d\W]+", stripped):
        errors.append(f"{field_name} value '{value}' looks like garbage")
        return False
    return True


def _validate_land_use(value, errors) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        errors.append("land_use must be a string or null")
        return False
    stripped = value.strip()
    if stripped == "":
        errors.append("land_use is an empty string, should be null instead")
        return False
    return True


# ---------------------------------------------------------------------------
# 2. Evidence grounding (hallucination prevention)
# ---------------------------------------------------------------------------

def check_evidence(record: dict, ocr_text: str) -> dict:
    """For every non-null field in `record`, check whether the value
    is actually supported by `ocr_text`.

    How "supported" is decided (kept intentionally simple and
    explainable for a judge):
      - We normalise both the OCR text and the candidate value
        (lowercase, unify spacing) so that small case/spacing
        differences don't cause false negatives.
      - A value is "supported" if that normalised value (or, for area,
        the numeric digits of it) appears as a substring of the
        normalised OCR text.
      - Numbers like khasra_number and area are compared on their
        digits/format directly, since an LLM might reformat spacing
        (e.g. "142 / 2" vs "142/2").

    This is deliberately a strict, literal check -- it is our defence
    against the LLM inventing values that sound plausible but are not
    actually written anywhere in the document.

    Returns:
        {
            "supported": {field: True/False/None, ...},  # None = field is null, N/A
            "unsupported_fields": [list of field names flagged as unsupported],
        }
    """
    normalised_text = _normalise(ocr_text)
    supported = {}
    unsupported_fields = []

    for field in REQUIRED_FIELDS:
        value = record.get(field)
        if value is None:
            supported[field] = None
            continue

        is_supported = _is_value_supported(field, value, normalised_text, ocr_text)
        supported[field] = is_supported
        if not is_supported:
            unsupported_fields.append(field)

    return {"supported": supported, "unsupported_fields": unsupported_fields}


def _normalise(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _is_value_supported(field: str, value, normalised_text: str, original_text: str) -> bool:
    if field == "area":
        # Compare digits only, tolerant of "1.25" vs "1.25 " etc.
        try:
            number_str = f"{float(value):g}"
        except (TypeError, ValueError):
            return False
        # Look for the number (allow both "1.25" and "1,25"-free variants).
        pattern = re.escape(str(value)) if isinstance(value, str) else re.escape(number_str)
        return bool(re.search(pattern.replace(r"\.0\b", ""), original_text)) or \
            str(value) in original_text or number_str in original_text

    if field in ("khasra_number",):
        # khasra numbers may have spacing differences; strip spaces
        # for the comparison.
        compact_value = re.sub(r"\s+", "", str(value)).lower()
        compact_text = re.sub(r"\s+", "", original_text).lower()
        return compact_value in compact_text

    if field == "area_unit":
        # area_unit may have been NORMALISED (e.g. Hindi "बीघा" ->
        # English "bigha", or "hectares" -> "hectare"). A normalised
        # value legitimately may not appear literally in the OCR
        # text, so "supported" here means: some known raw spelling
        # that maps to this normalised value appears in the text.
        # This is intentional normalisation (documented in the
        # README), not hallucination.
        normalised_value = str(value).lower()
        if normalised_value in normalised_text:
            return True
        for raw_word, mapped in KNOWN_AREA_UNITS.items():
            if mapped.lower() == normalised_value and raw_word.lower() in original_text.lower():
                return True
        return False

    # Generic string fields: owner_name, village, tehsil, district,
    # land_use, area_unit
    normalised_value = _normalise(str(value))
    return normalised_value in normalised_text
