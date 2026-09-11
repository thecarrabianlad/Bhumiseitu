"""
Orchestrates the document -> land record pipeline:

    document bytes --> OCR --> extraction --> confidence scoring --> DB

This module is the "glue" the backend owns. It depends only on the
abstract service interfaces (`OCRService`, `ExtractionService`,
`ConfidenceService`), never on a specific OCR/LLM implementation --
so P4 and P5 can land their real implementations independently without
touching this file (only the `get_*_service()` factory functions change).
"""
import logging
from typing import Any, Dict

from app.schemas.document import DocumentStatus
from app.schemas.record import RecordStatus
from app.services import records_service
from app.services.confidence.interface import get_confidence_service
from app.services.extraction.interface import get_extraction_service
from app.services.ocr.interface import get_ocr_service

logger = logging.getLogger(__name__)


async def run_pipeline_for_document(document_id: str) -> Dict[str, Any]:
    """
    Runs OCR -> extraction -> confidence scoring for a stored document and
    creates the resulting land record. Returns the created record dict.

    Raises whatever exception occurs after marking the document as FAILED,
    so the calling route can translate it into an HTTP error.
    """
    document = records_service.get_document(document_id)
    records_service.update_document_status(document_id, DocumentStatus.PROCESSING)

    try:
        # NOTE: in a real deployment, fetch the actual file bytes from
        # Supabase Storage using document["storage_path"] here. Left as a
        # placeholder call so this module doesn't hard-code a storage
        # client dependency beyond what's needed for OCR.
        file_bytes = _fetch_file_bytes(document["storage_path"])

        ocr_service = get_ocr_service()
        ocr_result = await ocr_service.extract_text(
            file_bytes=file_bytes, content_type=document["content_type"]
        )

        extraction_service = get_extraction_service()
        extracted_fields = await extraction_service.extract_fields(ocr_result.raw_text)

        confidence_service = get_confidence_service()
        overall_confidence, low_confidence_fields, needs_review = confidence_service.evaluate(
            extracted_fields
        )

        record_status = RecordStatus.NEEDS_REVIEW if needs_review else RecordStatus.APPROVED
        fields_as_dict = {name: field.model_dump() for name, field in extracted_fields.items()}

        record = records_service.create_record(
            document_id=document_id,
            status=record_status,
            fields=fields_as_dict,
            overall_confidence=overall_confidence,
            low_confidence_fields=low_confidence_fields,
            raw_ocr_text=ocr_result.raw_text,
        )

        records_service.update_document_status(document_id, DocumentStatus.PROCESSED)
        return record

    except Exception as exc:  # noqa: BLE001 -- deliberately broad: any failure marks doc FAILED
        logger.exception("Pipeline failed for document %s", document_id)
        records_service.update_document_status(
            document_id, DocumentStatus.FAILED, error_message=str(exc)
        )
        raise


def _fetch_file_bytes(storage_path: str) -> bytes:
    """
    Placeholder for downloading the original file from Supabase Storage.
    Replace with a real `supabase.storage.from_(...).download(...)` call
    once storage wiring is finalized -- kept isolated here so OCR/extraction
    code never needs to know about storage details.
    """
    raise NotImplementedError(
        "Wire up Supabase Storage download here (see app/db/storage.py for the upload side)."
    )
