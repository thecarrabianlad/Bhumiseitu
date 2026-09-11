from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.common import APIResponse, PaginationMeta
from app.schemas.record import LandRecordListItem, RecordStatus
from app.schemas.review import ReviewDecisionRequest, ReviewDecisionResponseData
from app.services import records_service
from app.services.mappers import row_to_list_item

router = APIRouter(prefix="/records", tags=["review"])


@router.get("/review", response_model=APIResponse[list[LandRecordListItem]])
async def list_records_requiring_review(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Lists land records currently flagged with status `needs_review`."""
    result = records_service.list_records_needing_review(limit=limit, offset=offset)
    items = [row_to_list_item(row) for row in result["items"]]

    return APIResponse(
        data=items,
        meta=PaginationMeta(total=result["total"], limit=limit, offset=offset),
    )


@router.post("/{record_id}/approve", response_model=APIResponse[ReviewDecisionResponseData])
async def approve_record(record_id: str, decision: ReviewDecisionRequest):
    """Approves a reviewed land record, optionally applying field corrections."""
    return _apply_decision(record_id, decision, RecordStatus.APPROVED)


@router.post("/{record_id}/reject", response_model=APIResponse[ReviewDecisionResponseData])
async def reject_record(record_id: str, decision: ReviewDecisionRequest):
    """Rejects a reviewed land record (e.g. unreadable scan, wrong document)."""
    return _apply_decision(record_id, decision, RecordStatus.REJECTED)


def _apply_decision(
    record_id: str, decision: ReviewDecisionRequest, new_status: RecordStatus
) -> APIResponse[ReviewDecisionResponseData]:
    try:
        updated = records_service.update_record_review_decision(
            record_id=record_id,
            new_status=new_status,
            reviewer_name=decision.reviewer_name,
            comments=decision.comments,
            corrected_fields=decision.corrected_fields,
        )
    except records_service.RecordNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    return APIResponse(
        data=ReviewDecisionResponseData(
            record_id=updated["id"],
            status=updated["status"],
            reviewer_name=updated["reviewer_name"],
        ),
        message=f"Record {new_status.value}.",
    )
