from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class DatabaseHealthResponse(BaseModel):
    status: str
    database: str
    connected: bool
    error: str | None = None


class AIComponentHealth(BaseModel):
    name: str
    status: str
    provider: str
    model: str | None = None
    ready: bool
    loaded: bool | None = None
    preload_enabled: bool | None = None
    error: str | None = None


class AIHealthResponse(BaseModel):
    status: str
    components: list[AIComponentHealth]
