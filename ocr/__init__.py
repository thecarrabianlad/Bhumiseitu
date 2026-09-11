"""
P3: Document Preprocessing + OCR pipeline for Bhumiseitu.

Usage:
    from ocr.pipeline import process_document
    result = process_document("/path/to/document.pdf")

See README.md ("OCR pipeline (P3)" section) for the full backend
integration guide and output schema.
"""
from .pipeline import process_document

__all__ = ["process_document"]
