from fastapi import APIRouter

from app.schemas.common import HealthResponse
from app.services.llm_service import check_llm_configured

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        llm_configured=check_llm_configured(),
    )
