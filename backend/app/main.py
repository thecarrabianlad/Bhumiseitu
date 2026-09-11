"""
FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload --port 8000

Interactive API docs (auto-generated from the Pydantic schemas + routes)
are then available at http://localhost:8000/docs
"""
import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.routes import documents, health, records, review
from app.schemas.common import APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for the Intelligent Land Record Digitization MVP. "
    "Connects the frontend to OCR, AI field extraction, and the Supabase database.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Every router is mounted under API_V1_PREFIX (default: /api/v1) so the
# frontend can version against a stable base path.
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(records.router, prefix=settings.API_V1_PREFIX)
app.include_router(review.router, prefix=settings.API_V1_PREFIX)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensures every error response -- not just success responses -- follows the APIError shape."""
    return JSONResponse(
        status_code=exc.status_code,
        content=APIError(message=str(exc.detail), error_code=_error_code_for_status(exc.status_code)).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=APIError(message="An unexpected error occurred.", error_code="INTERNAL_ERROR").model_dump(),
    )


def _error_code_for_status(status_code: int) -> str:
    return {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_501_NOT_IMPLEMENTED: "NOT_IMPLEMENTED",
    }.get(status_code, "ERROR")


@app.get("/")
async def root():
    return {"service": settings.APP_NAME, "status": "running", "docs": "/docs"}
