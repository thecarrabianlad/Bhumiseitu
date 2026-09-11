"""
Converts raw Supabase row dicts into the Pydantic response schemas.
Shared by `routes/records.py` and `routes/review.py` so both stay in sync
with the DB row shape.
"""
from typing import Optional

from app.schemas.record import LandRecordDetail, LandRecordListItem


def row_to_list_item(row: dict) -> LandRecordListItem:
    fields = row.get("fields") or {}
    return LandRecordListItem(
        id=row["id"],
        document_id=row["document_id"],
        status=row["status"],
        owner_name=_field_value(fields, "owner_name"),
        survey_number=_field_value(fields, "survey_number"),
        village=_field_value(fields, "village"),
        district=_field_value(fields, "district"),
        overall_confidence=row.get("overall_confidence"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_detail(row: dict) -> LandRecordDetail:
    return LandRecordDetail(
        id=row["id"],
        document_id=row["document_id"],
        status=row["status"],
        fields=row.get("fields") or {},
        overall_confidence=row.get("overall_confidence"),
        low_confidence_fields=row.get("low_confidence_fields") or [],
        raw_ocr_text=row.get("raw_ocr_text"),
        reviewer_name=row.get("reviewer_name"),
        review_comments=row.get("review_comments"),
        reviewed_at=row.get("reviewed_at"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _field_value(fields: dict, name: str) -> Optional[str]:
    entry = fields.get(name)
    if isinstance(entry, dict):
        return entry.get("value")
    return None
