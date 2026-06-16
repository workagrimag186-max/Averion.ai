from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.conversations import router as conversations_router
from app.api.documents import router as documents_router
from app.api.feedback import router as feedback_router
from app.api.health import router as health_router
from app.api.transcription import router as transcription_router
from app.api.users import router as users_router
from app.ai.embeddings import preload_embedding_model
from app.core.config import settings
from app.core.middleware import RequestSecurityMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.embedding_model_preload:
        preload_embedding_model()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API and AI service for Averion.ai.",
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    app.add_middleware(RequestSecurityMiddleware)

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
