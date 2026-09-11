"""
Schemas for the raw uploaded document (the scanned/photographed file),
as distinct from the structured `LandRecord` extracted from it.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"          # file stored, nothing processed yet
    PROCESSING = "processing"      # OCR/extraction pipeline running
    PROCESSED = "processed"        # pipeline finished, record(s) created
    FAILED = "failed"              # pipeline errored out


class DocumentOut(BaseModel):
    """Representation of a document row returned to clients."""
    id: str = Field(..., description="Document UUID")
    original_filename: str
    content_type: str
    storage_path: str = Field(..., description="Path/key of the file in Supabase Storage")
    status: DocumentStatus
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = Field(
        None, description="Populated when status == 'failed'"
    )

    model_config = {"from_attributes": True}


class DocumentUploadResponseData(BaseModel):
    document_id: str
    original_filename: str
    status: DocumentStatus
    storage_path: str


class ProcessDocumentResponseData(BaseModel):
    document_id: str
    status: DocumentStatus
    record_id: Optional[str] = Field(
        None, description="ID of the land record created/updated by this processing run"
    )
    needs_review: Optional[bool] = Field(
        None, description="Whether the resulting record was flagged for manual review"
    )
