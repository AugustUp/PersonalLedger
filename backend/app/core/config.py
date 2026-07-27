"""Application configuration via pydantic-settings.

All environment-related configuration is read from environment variables or a
local ``.env`` file. Secrets (JWT key, real paths) must never be committed.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ops Ledger"
    environment: str = "development"
    database_url: str = "sqlite:///../data/ops_ledger.db"

    # Security
    secret_key: str = "change-me-in-production-please-use-a-random-32-byte-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # Files
    upload_dir: str = "./uploads"
    max_upload_mb: int = 20

    # Logging
    log_dir: str = "./logs"

    # CORS (comma or newline separated list of allowed origins)
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
