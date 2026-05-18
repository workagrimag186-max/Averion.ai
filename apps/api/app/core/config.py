from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Averion.ai API"
    app_version: str = "0.1.0"
    service_name: str = "averion-api"
    database_url: str | None = None
    default_organization_id: str = "00000000-0000-0000-0000-000000000001"
    upload_dir: str = "./uploads"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    vector_db_path: str = "./vector_store"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    retrieval_top_k: int = 5
    llm_provider: str = "placeholder"
    llm_provider_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
