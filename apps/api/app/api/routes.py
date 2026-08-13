from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.schemas.health import HealthResponse
from app.services.health import HealthService

router = APIRouter()


def get_health_service() -> HealthService:
    from app.main import get_app_health_service

    return get_app_health_service()


@router.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"service": "ahara-api", "message": "Ahara API is running."}


@router.get("/health", response_model=HealthResponse, tags=["system"])
@router.get("/api/v1/health", response_model=HealthResponse, tags=["system"])
def health(health_service: HealthService = Depends(get_health_service)) -> HealthResponse | JSONResponse:
    report = health_service.get_health()
    if report.status == "healthy":
        return report
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=report.model_dump())
