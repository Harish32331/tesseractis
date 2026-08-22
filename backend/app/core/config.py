"""
Central application configuration.

All secrets and environment-dependent values are read from environment
variables via pydantic-settings. Nothing sensitive is hard-coded here.
See /.env.example at the repo root for the full list of variables.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "The Tesseractis API"
    ENVIRONMENT: str = "development"  # development | test | production
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://tesseractis:tesseractis@localhost:5432/tesseractis"

    # --- Redis (rate limiting / cache) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Auth / sessions ---
    SESSION_SECRET: str = "CHANGE_ME_IN_PRODUCTION"  # overridden by real env var in prod
    SESSION_COOKIE_NAME: str = "tesseractis_session"
    SESSION_TTL_SECONDS: int = 60 * 60 * 24 * 7  # 7 days
    SESSION_COOKIE_SECURE: bool = False  # must be True in production (HTTPS)

    # --- Upload / image security ---
    MAX_UPLOAD_BYTES: int = 8 * 1024 * 1024  # 8 MB
    MAX_IMAGE_DIMENSION_PX: int = 6000
    ALLOWED_IMAGE_MIME_TYPES: tuple[str, ...] = ("image/jpeg", "image/png", "image/webp")

    # --- Object storage (S3-compatible; MinIO for local dev) ---
    STORAGE_ENDPOINT_URL: str = "http://localhost:9000"
    STORAGE_BUCKET: str = "tesseractis-scans"
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""

    # --- AI provider ---
    AI_PROVIDER: str = "mock"  # "mock" | "real" — real requires AI_API_KEY to be set
    AI_API_KEY: str = ""
    AI_CONFIDENCE_LOW_THRESHOLD: float = 0.45
    AI_CONFIDENCE_HIGH_THRESHOLD: float = 0.75

    # --- CORS ---
    # Comma-separated list of allowed origins, e.g.
    # "https://tesseractis.vercel.app,http://localhost:3000"
    CORS_ALLOWED_ORIGINS_RAW: str = "http://localhost:3000"

    # --- Rate limiting (requests per window) ---
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 6

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS_RAW.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
