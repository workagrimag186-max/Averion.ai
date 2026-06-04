from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.conversations import router as conversations_router
from app.api.documents import router as documents_router
from app.api.feedback import router as feedback_router
from app.api.health import router as health_router
from app.api.transcription import router as transcription_router
from app.api.users import router as users_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API and AI service for Averion.ai."
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    app.include_router(health_router)
    app.include_router(documents_router)
    app.include_router(chat_router)
    app.include_router(conversations_router)
    app.include_router(feedback_router)
    app.include_router(transcription_router)
    app.include_router(users_router)

    @app.get("/", tags=["root"])
    def read_root() -> dict[str, str]:
        return {
            "message": "Averion.ai API",
            "docs_url": "/docs",
            "health_url": "/health"
        }

    return app


app = create_app()
