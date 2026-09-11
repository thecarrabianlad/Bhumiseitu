"""
schemas.py
----------
This file defines the FIXED shape of the data that P3 produces.

Why does this file exist?
    Every other file in this project (validator, confidence, router,
    tests) needs to agree on exactly what fields exist in a land
    record. Instead of repeating that list everywhere, we define it
    once here and import it everywhere else.

Beginner note:
    Think of this as a "form template" with 8 blank fields. No matter
    what the OCR text looks like, P3 always hands back a form with
    these same 8 blanks. If information is missing, the blank stays
    as null (Python's None) -- we never delete a blank and we never
    add a new blank.
"""

from typing import Optional, TypedDict


# The 8 fields are fixed by the project requirements. Do not add or
# remove fields here without updating validator.py, confidence.py and
# the tests, since they all assume exactly this set of keys.
REQUIRED_FIELDS = [
    "owner_name",
    "khasra_number",
    "area",
    "area_unit",
    "village",
    "tehsil",
    "district",
    "land_use",
]


class LandRecord(TypedDict, total=False):
    """Type hint only (for editors / readability). Not enforced at
    runtime -- validator.py does the real runtime checking."""
    owner_name: Optional[str]
    khasra_number: Optional[str]
    area: Optional[float]
    area_unit: Optional[str]
    village: Optional[str]
    tehsil: Optional[str]
    district: Optional[str]
    land_use: Optional[str]


def empty_record() -> dict:
    """Return a brand-new record with every field set to null.

    Used as the safe fallback whenever something goes wrong (e.g. the
    LLM returns broken JSON) -- we would rather return "we found
    nothing" than crash or invent data.
    """
    return {field: None for field in REQUIRED_FIELDS}


# Units we recognise and how we normalise them. Extend this dict if
# your land records use other units (e.g. "bigha", "kanal").
KNOWN_AREA_UNITS = {
    "hectare": "hectare",
    "hectares": "hectare",
    "ha": "hectare",
    "acre": "acre",
    "acres": "acre",
    "sq m": "sq_m",
    "sqm": "sq_m",
    "sq. m": "sq_m",
    "square meter": "sq_m",
    "square metre": "sq_m",
    "बीघा": "bigha",
    "bigha": "bigha",
    "हेक्टेयर": "hectare",
    "एकड़": "acre",
}
