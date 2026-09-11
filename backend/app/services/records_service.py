"""
Data-access layer for `documents` and `land_records` tables in Supabase.

This is the ONLY module (besides `app/db/supabase_client.py`) that should
construct Supabase queries. Routes call these functions -- they never talk
to `get_supabase()` directly. That keeps the DB schema/query details in
one place if the Supabase table structure changes.

Expected table shapes (adjust to match whatever the DB owner sets up in
Supabase, then update the queries below accordingly):

documents
  id (uuid, pk), original_filename (text), content_type (text),
  storage_path (text), status (text), uploaded_at (timestamptz),
  processed_at (timestamptz, nullable), error_message (text, nullable)

land_records
  id (uuid, pk), document_id (uuid, fk -> documents.id), status (text),
  fields (jsonb), overall_confidence (float, nullable),
  low_confidence_fields (jsonb / text[]), raw_ocr_text (text, nullable),
  reviewer_name (text, nullable), review_comments (text, nullable),
  reviewed_at (timestamptz, nullable),
  created_at (timestamptz), updated_at (timestamptz)
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.db.supabase_client import get_supabase
from app.schemas.document import DocumentStatus
from app.schemas.record import RecordStatus


class RecordNotFoundError(Exception):
    pass


class DocumentNotFoundError(Exception):
    pass


def _settings():
    return get_settings()


# --------------------------------------------------------------------------
# Documents
# --------------------------------------------------------------------------

def create_document(
    original_filename: str,
    content_type: str,
    storage_path: str,
) -> Dict[str, Any]:
    settings = _settings()
    supabase = get_supabase()

    payload = {
        "id": str(uuid.uuid4()),
        "original_filename": original_filename,
        "content_type": content_type,
        "storage_path": storage_path,
        "status": DocumentStatus.UPLOADED.value,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    result = supabase.table(settings.SUPABASE_DOCUMENTS_TABLE).insert(payload).execute()
    return result.data[0]


def get_document(document_id: str) -> Dict[str, Any]:
    settings = _settings()
    supabase = get_supabase()

    result = (
        supabase.table(settings.SUPABASE_DOCUMENTS_TABLE)
        .select("*")
        .eq("id", document_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise DocumentNotFoundError(f"Document {document_id} not found")
    return result.data[0]


def update_document_status(
    document_id: str,
    status: DocumentStatus,
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    settings = _settings()
    supabase = get_supabase()

    update_payload: Dict[str, Any] = {"status": status.value}
    if status == DocumentStatus.PROCESSED:
        update_payload["processed_at"] = datetime.now(timezone.utc).isoformat()
    if error_message is not None:
        update_payload["error_message"] = error_message

    result = (
        supabase.table(settings.SUPABASE_DOCUMENTS_TABLE)
        .update(update_payload)
        .eq("id", document_id)
        .execute()
    )
    if not result.data:
        raise DocumentNotFoundError(f"Document {document_id} not found")
    return result.data[0]


# --------------------------------------------------------------------------
# Land records
# --------------------------------------------------------------------------

def create_record(
    document_id: str,
    status: RecordStatus,
    fields: Dict[str, Any],
    overall_confidence: Optional[float],
    low_confidence_fields: List[str],
    raw_ocr_text: Optional[str],
) -> Dict[str, Any]:
    settings = _settings()
    supabase = get_supabase()

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "id": str(uuid.uuid4()),
        "document_id": document_id,
        "status": status.value,
        "fields": fields,
        "overall_confidence": overall_confidence,
        "low_confidence_fields": low_confidence_fields,
        "raw_ocr_text": raw_ocr_text,
        "created_at": now,
        "updated_at": now,
    }
    result = supabase.table(settings.SUPABASE_RECORDS_TABLE).insert(payload).execute()
    return result.data[0]


def get_record(record_id: str) -> Dict[str, Any]:
    settings = _settings()
    supabase = get_supabase()

    result = (
        supabase.table(settings.SUPABASE_RECORDS_TABLE)
        .select("*")
        .eq("id", record_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise RecordNotFoundError(f"Land record {record_id} not found")
    return result.data[0]


def list_records(
    limit: int = 20,
    offset: int = 0,
    status: Optional[RecordStatus] = None,
    district: Optional[str] = None,
) -> Dict[str, Any]:
    """Returns {"items": [...], "total": int} for the list endpoint."""
    settings = _settings()
    supabase = get_supabase()

    query = supabase.table(settings.SUPABASE_RECORDS_TABLE).select("*", count="exact")
    if status is not None:
        query = query.eq("status", status.value)
    # NOTE: filtering on a jsonb field like `fields->>district` depends on
    # exact Supabase/PostgREST syntax for your schema -- adjust once the
    # real `fields` JSON shape is finalized with P5.
    if district is not None:
        query = query.eq("fields->>district", district)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
    result = query.execute()
    return {"items": result.data, "total": result.count or 0}


def list_records_needing_review(limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    return list_records(limit=limit, offset=offset, status=RecordStatus.NEEDS_REVIEW)


def update_record_review_decision(
    record_id: str,
    new_status: RecordStatus,
    reviewer_name: str,
    comments: Optional[str],
    corrected_fields: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    settings = _settings()
    supabase = get_supabase()

    update_payload: Dict[str, Any] = {
        "status": new_status.value,
        "reviewer_name": reviewer_name,
        "review_comments": comments,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if corrected_fields:
        # Merge corrections into existing `fields` JSON.
        current = get_record(record_id)
        merged_fields = {**current.get("fields", {}), **corrected_fields}
        update_payload["fields"] = merged_fields

    result = (
        supabase.table(settings.SUPABASE_RECORDS_TABLE)
        .update(update_payload)
        .eq("id", record_id)
        .execute()
    )
    if not result.data:
        raise RecordNotFoundError(f"Land record {record_id} not found")
    return result.data[0]
