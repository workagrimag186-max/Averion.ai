from fastapi import APIRouter

from app.core.config import settings
from app.db.connection import check_database_connection
from app.schemas.health import DatabaseHealthResponse, HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.app_version
    )


@router.get("/health/database", response_model=DatabaseHealthResponse)
def database_health_check() -> DatabaseHealthResponse:
    connection_check = check_database_connection()

    return DatabaseHealthResponse(
        status="ok" if connection_check.connected else "degraded",
        database="postgres",
        connected=connection_check.connected,
        error=connection_check.error
    )
