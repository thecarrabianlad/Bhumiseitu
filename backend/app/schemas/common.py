"""
Shared response envelope used by every endpoint in the API.

Keeping ONE response shape across the whole backend means the frontend
(P... whoever owns frontend/) can write a single response handler instead
of guessing the shape per-endpoint.

Success:
{
  "success": true,
  "data": {...} | [...],
  "message": "optional human-readable message",
  "meta": {...}   // optional, e.g. pagination
}

Failure:
{
  "success": false,
  "data": null,
  "message": "human-readable error message",
  "error_code": "SOME_ERROR_CODE"
}
"""
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int = Field(..., description="Total number of matching records")
    limit: int = Field(..., description="Page size used for this response")
    offset: int = Field(..., description="Offset used for this response")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    meta: Optional[PaginationMeta] = None


class APIError(BaseModel):
    success: bool = False
    data: None = None
    message: str
    error_code: str = "INTERNAL_ERROR"
