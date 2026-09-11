"""
Field extraction service interface -- P5 implements this.

HOW TO PLUG IN (for P5):
1. Create a new module in this package (e.g. `llm_extractor.py`) that
   subclasses `ExtractionService` and implements `extract_fields()`.
   Whatever LLM/NLP approach you use, the output must be a dict of
   field_name -> ExtractedField(value=..., confidence=...).
2. Update `get_extraction_service()` at the bottom of this file.
3. Field names you return should line up with `LandRecordFields` in
   `app/schemas/record.py` where possible (owner_name, survey_number,
   village, district, state, area, land_type, etc). Anything that
   doesn't fit the fixed schema will be preserved under `extra_fields`.
"""
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Dict

from app.schemas.record import ExtractedField


class ExtractionService(ABC):
    """Abstract base class every concrete extraction implementation must extend."""

    @abstractmethod
    async def extract_fields(self, raw_ocr_text: str) -> Dict[str, ExtractedField]:
        """
        Parse structured land-record fields out of raw OCR text.

        Args:
            raw_ocr_text: The text returned by the OCR service.

        Returns:
            Dict mapping field name -> ExtractedField(value, confidence).
            `confidence` should be a per-field float in [0, 1] representing
            how sure the extraction model is about that value.
        """
        raise NotImplementedError


class PlaceholderExtractionService(ExtractionService):
    """
    Temporary stand-in so the API is runnable end-to-end before P5's real
    extraction logic is wired in. Returns empty/low-confidence fields so
    every record flows into the "needs review" queue by default.
    """

    async def extract_fields(self, raw_ocr_text: str) -> Dict[str, ExtractedField]:
        return {
            "owner_name": ExtractedField(value=None, confidence=0.0),
            "survey_number": ExtractedField(value=None, confidence=0.0),
            "village": ExtractedField(value=None, confidence=0.0),
            "district": ExtractedField(value=None, confidence=0.0),
        }


@lru_cache
def get_extraction_service() -> ExtractionService:
    """
    Dependency-injection point. Swap the returned class here once a real
    extraction implementation exists.
    """
    return PlaceholderExtractionService()
