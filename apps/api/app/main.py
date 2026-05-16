from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API and AI service for Averion.ai."
    )

    app.include_router(health_router)

    @app.get("/", tags=["root"])
    def read_root() -> dict[str, str]:
        return {
            "message": "Averion.ai API",
            "docs_url": "/docs",
            "health_url": "/health"
        }

    return app


app = create_app()
