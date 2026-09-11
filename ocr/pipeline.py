"""
P3: Document Preprocessing + OCR pipeline.

Public API
----------
    process_document(input_path) -> dict

This module has no FastAPI (or any web framework) dependency — it is a
plain Python core that takes a file path and returns a JSON-serializable
dict. The API layer is expected to own upload/storage/HTTP concerns only
and call `process_document` with a local file path once a file is saved.

Scope: this module performs preprocessing + OCR ONLY. It intentionally
does not do entity/field extraction, LLM calls, or any land-record
semantic parsing — that is P5's responsibility and consumes this module's
output.
"""
import os
import traceback
from typing import List, Optional

import numpy as np

from .pdf_utils import PDFConversionError, pdf_to_images
from .preprocessing import ImageLoadError, load_image, preprocess_image
from .schemas import OCRDocumentResult, OCRLine, OCRPage, build_error_result, build_success_result

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS

# --- OCR language configuration -------------------------------------------
# Centralized here (and overridable via the OCR_LANG env var) so switching
# the recognition language later is a one-line change, not a code hunt.
# PaddleOCR loads one language model per engine instance; "en" and "hi" are
# both supported out of the box for this project's English/Hindi prototype
# documents. See the module docstring in README / P3 integration notes for
# the current limitation around mixed-script single-pass OCR.
DEFAULT_OCR_LANG = os.environ.get("OCR_LANG", "en")

# Lazily-created, reused PaddleOCR engine(s), keyed by language, so we never
# pay model-load cost per image/line — only once per language per process.
_ocr_engines = {}


def _get_ocr_engine(lang: str):
    """Return a cached PaddleOCR engine for `lang`, creating it on first use."""
    if lang in _ocr_engines:
        return _ocr_engines[lang]

    # Imported lazily so this module (and the rest of the pipeline) can
    # still be imported/tested even in environments where paddleocr isn't
    # installed yet.
    from paddleocr import PaddleOCR

    engine = PaddleOCR(lang=lang)
    _ocr_engines[lang] = engine
    return engine


def _run_ocr_on_image(image: np.ndarray, lang: str) -> dict:
    """
    Run the PaddleOCR engine on a single preprocessed image and return its
    raw (dict-like) result for page 1 of that image.

    Uses PaddleOCR's current `.predict()` API (PaddleOCR >= 3.x), which
    returns dict-like result objects exposing `rec_texts`, `rec_scores`,
    and `rec_polys` — NOT the older/deprecated `.ocr()` line-tuple format.
    """
    engine = _get_ocr_engine(lang)
    results = engine.predict(image)
    if not results:
        return {"rec_texts": [], "rec_scores": [], "rec_polys": []}
    return results[0]


def _to_bbox_list(poly) -> List[List[float]]:
    """Normalize a single polygon (numpy array or list of points) to plain lists."""
    if poly is None:
        return []
    if hasattr(poly, "tolist"):
        poly = poly.tolist()
    return [[float(x), float(y)] for x, y in poly]


def _build_page(raw_result: dict, page_number: int, lang: str) -> OCRPage:
    """Convert a raw PaddleOCR result for one image into a standardized OCRPage."""
    texts = list(raw_result.get("rec_texts", []) or [])
    scores = list(raw_result.get("rec_scores", []) or [])
    polys = list(raw_result.get("rec_polys", []) or [])

    lines: List[OCRLine] = []
    for i, text in enumerate(texts):
        confidence = float(scores[i]) if i < len(scores) and scores[i] is not None else None
        bbox = _to_bbox_list(polys[i]) if i < len(polys) else []
        lines.append({"text": text, "confidence": confidence, "bbox": bbox})

    full_text = "\n".join(texts)
    numeric_scores = [s for s in scores if s is not None]
    average_confidence = round(sum(numeric_scores) / len(numeric_scores), 4) if numeric_scores else None

    # PaddleOCR (as installed) does not expose a per-line detected
    # language in its result — only the language the engine was
    # configured with. Per the spec, fall back to that configured value
    # rather than guessing.
    return {
        "page": page_number,
        "text": full_text,
        "average_confidence": average_confidence,
        "language": lang,
        "lines": lines,
    }


def _process_single_image(
    image: np.ndarray, page_number: int, lang: str, apply_binarization: bool
) -> OCRPage:
    cleaned = preprocess_image(image, apply_binarization=apply_binarization)
    raw_result = _run_ocr_on_image(cleaned, lang)
    return _build_page(raw_result, page_number, lang)


def _process_image_file(path: str, lang: str, apply_binarization: bool) -> OCRDocumentResult:
    try:
        image = load_image(path)
    except ImageLoadError as exc:
        return build_error_result("image", str(exc))

    page = _process_single_image(image, 1, lang, apply_binarization)
    return build_success_result("image", [page])


def _process_pdf(path: str, lang: str, apply_binarization: bool) -> OCRDocumentResult:
    try:
        page_images = pdf_to_images(path)
    except PDFConversionError as exc:
        return build_error_result("pdf", str(exc))

    pages = [
        _process_single_image(img, i + 1, lang, apply_binarization)
        for i, img in enumerate(page_images)
    ]
    return build_success_result("pdf", pages)


def process_document(
    input_path: str,
    lang: Optional[str] = None,
    apply_binarization: bool = False,
) -> OCRDocumentResult:
    """
    Run the full P3 pipeline (load -> preprocess -> OCR) on a single
    document and return a standardized, JSON-serializable dict:

        {
          "success": bool,
          "document_type": "image" | "pdf" | "unknown",
          "pages": [
            {
              "page": 1,
              "text": "...",
              "average_confidence": 0.91,
              "language": "en",
              "lines": [{"text": "...", "confidence": 0.94, "bbox": [[x,y], ...]}]
            }
          ],
          "error": null
        }

    Args:
        input_path: path to a .jpg/.jpeg/.png/.pdf file on disk.
        lang: OCR language code (e.g. "en", "hi"). Defaults to
            DEFAULT_OCR_LANG (env var OCR_LANG, or "en").
        apply_binarization: opt-in hard-thresholding preprocessing stage;
            off by default to avoid destroying faded text on old scans.

    This function never raises for expected failure modes (missing file,
    unsupported type, corrupt image, PDF conversion failure, OCR failure)
    — it always returns the schema above with success=False and a
    human-readable `error`, with no raw stack trace exposed.
    """
    lang = lang or DEFAULT_OCR_LANG

    if not input_path or not os.path.isfile(input_path):
        return build_error_result("unknown", f"File not found: {input_path}")

    ext = os.path.splitext(input_path)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        return build_error_result(
            "unknown",
            f"Unsupported file type '{ext}'. Supported types: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    doc_type = "pdf" if ext in SUPPORTED_PDF_EXTENSIONS else "image"

    try:
        if ext in SUPPORTED_PDF_EXTENSIONS:
            return _process_pdf(input_path, lang, apply_binarization)
        return _process_image_file(input_path, lang, apply_binarization)
    except Exception as exc:  # noqa: BLE001 - top-level safety net
        # Log full details server-side for debugging, but never return a
        # raw traceback through the public API result.
        traceback.print_exc()
        return build_error_result(doc_type, f"OCR pipeline failed: {exc}")
