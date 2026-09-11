"""
PDF handling utilities for the OCR pipeline.

PDFs are rasterized page-by-page into OpenCV-compatible (BGR) images via
`pdf2image` (which shells out to poppler's `pdftoppm`), so the rest of the
pipeline (preprocessing + OCR) can treat every PDF page exactly like a
standalone image.
"""
from typing import List

import numpy as np


class PDFConversionError(Exception):
    """Raised when a PDF cannot be rasterized into page images."""


def is_pdf(path: str) -> bool:
    return path.lower().endswith(".pdf")


def pdf_to_images(pdf_path: str, dpi: int = 300) -> List[np.ndarray]:
    """
    Convert every page of a PDF into a BGR numpy array (OpenCV's format).

    Raises PDFConversionError on any failure (missing poppler binaries,
    corrupt/encrypted PDF, unreadable pages, etc.) so callers get a single
    predictable exception type rather than needing to know pdf2image's
    internals.
    """
    try:
        from pdf2image import convert_from_path
        from pdf2image.exceptions import (
            PDFInfoNotInstalledError,
            PDFPageCountError,
            PDFSyntaxError,
        )
    except ImportError as exc:
        raise PDFConversionError(
            "PDF support requires 'pdf2image' (and system package "
            "'poppler-utils') to be installed."
        ) from exc

    try:
        pil_pages = convert_from_path(pdf_path, dpi=dpi)
    except (PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError) as exc:
        raise PDFConversionError(f"Failed to convert PDF '{pdf_path}': {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - normalize any other failure
        raise PDFConversionError(f"Failed to convert PDF '{pdf_path}': {exc}") from exc

    if not pil_pages:
        raise PDFConversionError(f"PDF '{pdf_path}' produced no pages.")

    images = []
    for page in pil_pages:
        rgb = np.array(page.convert("RGB"))
        bgr = rgb[:, :, ::-1].copy()
        images.append(bgr)
    return images
