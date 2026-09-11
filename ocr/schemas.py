"""
Standardized, JSON-compatible output schema for the OCR pipeline (P3).

Every call to `ocr.pipeline.process_document` returns a dict shaped like
either `build_success_result(...)` or `build_error_result(...)` below, so
downstream consumers (the FastAPI backend, P5's extraction stage) can rely
on a single predictable contract regardless of input type (image or PDF)
or whether OCR succeeded.
"""
from typing import List, Optional, TypedDict


class OCRLine(TypedDict):
    """A single recognized line/text region within a page."""

    text: str
    confidence: Optional[float]
    bbox: List[List[float]]  # 4 points: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]


class OCRPage(TypedDict):
    """OCR output for a single page (a standalone image counts as one page)."""

    page: int
    text: str
    average_confidence: Optional[float]
    language: Optional[str]
    lines: List[OCRLine]


class OCRDocumentResult(TypedDict):
    """Top-level return value of `process_document`."""

    success: bool
    document_type: str  # "image" | "pdf" | "unknown"
    pages: List[OCRPage]
    error: Optional[str]


def build_success_result(document_type: str, pages: List[OCRPage]) -> OCRDocumentResult:
    """Build the standardized success payload."""
    return {
        "success": True,
        "document_type": document_type,
        "pages": pages,
        "error": None,
    }


def build_error_result(document_type: str, error_message: str) -> OCRDocumentResult:
    """
    Build the standardized failure payload.

    `error_message` should be a short, human-readable explanation — never a
    raw stack trace or internal exception repr — so it is safe to surface
    through an API response.
    """
    return {
        "success": False,
        "document_type": document_type,
        "pages": [],
        "error": str(error_message),
    }
