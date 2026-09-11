import os

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.db.storage import upload_document_file
from app.schemas.common import APIResponse
from app.schemas.document import (
    DocumentStatus,
    DocumentUploadResponseData,
    ProcessDocumentResponseData,
)
from app.services import records_service
from app.services.pipeline import run_pipeline_for_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=APIResponse[DocumentUploadResponseData],
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads a scanned land record (image or PDF) to storage and creates a
    `documents` row with status `uploaded`. Does NOT run OCR/extraction --
    call `POST /documents/{document_id}/process` next.
    """
    settings = get_settings()

    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{extension}'. Allowed: {settings.allowed_extensions_list}",
        )

    file_bytes = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds max upload size of {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    storage_path = upload_document_file(
        file_bytes=file_bytes,
        original_filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
    )

    document = records_service.create_document(
        original_filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        storage_path=storage_path,
    )

    return APIResponse(
        data=DocumentUploadResponseData(
            document_id=document["id"],
            original_filename=document["original_filename"],
            status=DocumentStatus(document["status"]),
            storage_path=document["storage_path"],
        ),
        message="Document uploaded successfully.",
    )


@router.post(
    "/{document_id}/process",
    response_model=APIResponse[ProcessDocumentResponseData],
)
async def process_document(document_id: str):
    """
    Runs the OCR -> extraction -> confidence pipeline for a previously
    uploaded document and creates the resulting land record.

    Until P4/P5 plug in real OCR/extraction implementations, this will
    complete using the placeholder services in `app/services/*/interface.py`.
    """
    try:
        record = await run_pipeline_for_document(document_id)
    except records_service.DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    except NotImplementedError as exc:
        # Expected until Supabase Storage download / real services are wired in.
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return APIResponse(
        data=ProcessDocumentResponseData(
            document_id=document_id,
            status=DocumentStatus.PROCESSED,
            record_id=record["id"],
            needs_review=record["status"] == "needs_review",
        ),
        message="Document processed successfully.",
    )
