"""Schemas for the human-review (approve/reject) workflow."""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.schemas.record import RecordStatus


class ReviewDecisionRequest(BaseModel):
    reviewer_name: str = Field(..., description="Name/ID of the person reviewing")
    comments: Optional[str] = None
    corrected_fields: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional field_name -> corrected_value map. If provided on "
        "approval, these overwrite the extracted values before saving.",
    )


class ReviewDecisionResponseData(BaseModel):
    record_id: str
    status: RecordStatus
    reviewer_name: str
