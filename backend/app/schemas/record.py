"""
Schemas for the structured `LandRecord` — the output of the OCR +
extraction + confidence pipeline, and the thing reviewers approve/reject.

Field names below (owner_name, survey_number, etc.) are a reasonable
starting point for Indian land records — adjust in coordination with
P4/P5 (extraction) once the real field list from the source documents
is finalized. Because `fields` is a free-form dict, extraction can add
new field keys without needing a backend schema change.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RecordStatus(str, Enum):
    PROCESSING = "processing"          # pipeline still running for this record
    NEEDS_REVIEW = "needs_review"      # low confidence on one or more fields
    APPROVED = "approved"              # reviewed and accepted
    REJECTED = "rejected"              # reviewed and rejected
    FAILED = "failed"                  # extraction/confidence step errored


class ExtractedField(BaseModel):
    """A single extracted value plus how confident the extraction service was."""
    value: Any = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)


# Common land-record fields, extracted from OCR text by the extraction service.
# `Dict[str, ExtractedField]` also lets extraction return arbitrary extra fields
# (e.g. "mutation_number") without a schema change.
class LandRecordFields(BaseModel):
    owner_name: Optional[ExtractedField] = None
    survey_number: Optional[ExtractedField] = None
    khasra_number: Optional[ExtractedField] = None
    village: Optional[ExtractedField] = None
    tehsil: Optional[ExtractedField] = None
    district: Optional[ExtractedField] = None
    state: Optional[ExtractedField] = None
    area: Optional[ExtractedField] = None
    area_unit: Optional[ExtractedField] = None
    land_type: Optional[ExtractedField] = None
    registration_date: Optional[ExtractedField] = None
    extra_fields: Dict[str, ExtractedField] = Field(
        default_factory=dict,
        description="Any additional fields the extraction service produces "
        "that aren't in the fixed schema above.",
    )


class LandRecordListItem(BaseModel):
    """Lightweight shape for the records list endpoint."""
    id: str
    document_id: str
    status: RecordStatus
    owner_name: Optional[str] = None
    survey_number: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    overall_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LandRecordDetail(BaseModel):
    """Full shape for the single-record endpoint."""
    id: str
    document_id: str
    status: RecordStatus
    fields: LandRecordFields
    overall_confidence: Optional[float] = Field(
        None, description="Aggregate confidence produced by the confidence service"
    )
    low_confidence_fields: list[str] = Field(
        default_factory=list,
        description="Names of fields below the review threshold",
    )
    raw_ocr_text: Optional[str] = Field(
        None, description="Raw text returned by OCR, kept for audit/debugging"
    )
    reviewer_name: Optional[str] = None
    review_comments: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
