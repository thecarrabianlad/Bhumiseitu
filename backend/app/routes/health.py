from fastapi import APIRouter

from app.schemas.common import APIResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return APIResponse(data={"status": "ok"}, message="Service is healthy.")
