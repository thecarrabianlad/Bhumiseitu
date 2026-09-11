"""
OCR service interface -- P4 implements this.

HOW TO PLUG IN (for P4):
1. Create a new module in this package (e.g. `tesseract_ocr.py` or
   `google_vision_ocr.py`) that subclasses `OCRService` and implements
   `extract_text()`.
2. Update `get_ocr_service()` at the bottom of this file to return your
   class instead of `PlaceholderOCRService`.
3. Nothing else in the codebase needs to change -- `pipeline.py` only
   depends on this interface, never a concrete implementation.
"""
from abc import ABC, abstractmethod
from functools import lru_cache

from pydantic import BaseModel


class OCRResult(BaseModel):
    """Standard shape every OCR implementation must return."""
    raw_text: str
    page_count: int = 1
    engine: str = "unknown"


class OCRService(ABC):
    """Abstract base class every concrete OCR implementation must extend."""

    @abstractmethod
    async def extract_text(self, file_bytes: bytes, content_type: str) -> OCRResult:
        """
        Run OCR on the given file bytes and return the extracted text.

        Args:
            file_bytes: Raw bytes of the uploaded document (image or PDF).
            content_type: MIME type of the file, e.g. "image/jpeg" or "application/pdf".

        Returns:
            OCRResult with the raw extracted text.
        """
        raise NotImplementedError


class PlaceholderOCRService(OCRService):
    """
    Temporary stand-in so the API is runnable end-to-end before P4's real
    OCR engine is wired in. Returns an obviously-fake result -- DO NOT use
    this in production.
    """

    async def extract_text(self, file_bytes: bytes, content_type: str) -> OCRResult:
        return OCRResult(
            raw_text="[PLACEHOLDER OCR OUTPUT -- replace PlaceholderOCRService with a real implementation]",
            page_count=1,
            engine="placeholder",
        )


@lru_cache
def get_ocr_service() -> OCRService:
    """
    Dependency-injection point. Swap the returned class here once a real
    OCR implementation exists -- routes/pipeline code should always call
    this function rather than instantiating a service directly.
    """
    return PlaceholderOCRService()
