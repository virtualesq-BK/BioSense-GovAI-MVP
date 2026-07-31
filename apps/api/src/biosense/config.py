from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_API_DIR = Path(__file__).resolve().parents[2]
_MONOREPO_ROOT = _API_DIR.parent.parent
_ENV_FILES = (
    _API_DIR / ".env",
    _MONOREPO_ROOT / ".env",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(p) for p in _ENV_FILES if p.is_file()],
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://biosense:biosense_dev@localhost:5432/biosense"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "biosense_dev"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    openai_api_key: str = ""
    openai_api_url: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Korean public data APIs
    kosis_api_key: str = ""
    kosis_base_url: str = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    kdca_api_key: str = ""
    kdca_api_url: str = ""
    kdca_base_url: str = "https://apis.data.go.kr/B552584/EssentialHealthIndicatorsService"

    # Ingestion pipeline
    ingestion_scheduler_enabled: bool = True
    ingestion_cron_hour: int = 3
    ingestion_cache_ttl_hours: int = 24
    ingestion_retry_max_attempts: int = 3
    ingestion_retry_base_delay_seconds: float = 1.0
    public_data_seed_path: str = "data/public_health/kr_cancer_stats.json"
    literature_upload_dir: str = "data/uploads/papers"
    literature_chunk_size: int = 512
    literature_chunk_overlap: int = 64
    literature_rag_top_k: int = 5

    @property
    def async_database_url(self) -> str:
        from biosense.infrastructure.database import to_asyncpg_url

        return to_asyncpg_url(self.database_url)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def has_kdca_api(self) -> bool:
        return bool(self.kdca_api_url or self.kdca_api_key)


settings = Settings()
