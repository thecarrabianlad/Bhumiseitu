"""
Centralized application configuration.

All environment-driven settings live here so the rest of the app never
touches `os.environ` directly. Copy `.env.example` to `.env` and fill in
real values before running.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_ENV: str = "development"
    APP_NAME: str = "Land Record Digitization API"
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # --- Supabase ---
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_DOCUMENTS_TABLE: str = "documents"
    SUPABASE_RECORDS_TABLE: str = "land_records"
    SUPABASE_STORAGE_BUCKET: str = "land-record-documents"

    # --- Uploads ---
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_UPLOAD_EXTENSIONS: str = ".pdf,.jpg,.jpeg,.png,.tiff"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_UPLOAD_EXTENSIONS.split(",") if ext.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — import and call this, don't instantiate Settings() directly."""
    return Settings()
