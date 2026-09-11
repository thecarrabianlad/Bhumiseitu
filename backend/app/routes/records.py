from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.common import APIResponse, PaginationMeta
from app.schemas.record import LandRecordDetail, LandRecordListItem, RecordStatus
from app.services import records_service
from app.services.mappers import row_to_detail, row_to_list_item

router = APIRouter(prefix="/records", tags=["records"])


@router.get("", response_model=APIResponse[list[LandRecordListItem]])
async def list_land_records(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[RecordStatus] = Query(None, alias="status"),
    district: Optional[str] = Query(None),
):
    """Lists land records with pagination and optional status/district filters."""
    result = records_service.list_records(
        limit=limit, offset=offset, status=status_filter, district=district
    )
    items = [row_to_list_item(row) for row in result["items"]]

    return APIResponse(
        data=items,
        meta=PaginationMeta(total=result["total"], limit=limit, offset=offset),
    )


@router.get("/{record_id}", response_model=APIResponse[LandRecordDetail])
async def get_land_record(record_id: str):
    """Fetches full detail (all fields + confidence) for a single land record."""
    try:
        row = records_service.get_record(record_id)
    except records_service.RecordNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    return APIResponse(data=row_to_detail(row))
