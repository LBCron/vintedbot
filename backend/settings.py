from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="backend/.env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    ENV: str = "dev"
    PORT: int = 5000
    
    # Database
    VINTEDBOT_DATABASE_URL: str = "sqlite:///backend/data/db.sqlite"
    
    # CORS
    ALLOWED_ORIGINS: str = "*"
    CORS_ORIGINS: List[str] = ["*"]
    
    # Encryption
    ENCRYPTION_KEY: str = "default-32-byte-key-change-this!"
    SECRET_KEY: str = "dev-secret"
    
    # Mock mode
    MOCK_MODE: bool = False
    
    # Scheduler
    SYNC_INTERVAL_MIN: int = 15
    PRICE_DROP_CRON: str = "0 3 * * *"
    PLAYWRIGHT_HEADLESS: bool = True
    JOBS_ENABLED: bool = True
    
    # Vinted session storage
    SESSION_STORE_PATH: str = "backend/data/session.enc"
    
    # Media storage configuration
    MEDIA_STORAGE: Literal["local", "s3"] = "local"
    MEDIA_ROOT: str = "backend/data/uploads"
    MEDIA_BASE_URL: str = "/media"
    
    # S3 configuration (for future use)
    S3_BUCKET: str | None = None
    S3_ENDPOINT_URL: str | None = None
    S3_REGION: str | None = None
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    
    # Upload policy
    MAX_UPLOADS_PER_REQUEST: int = 20
    MAX_FILE_SIZE_MB: int = 15
    ALLOWED_MIME_PREFIXES: List[str] = ["image/"]
    JPEG_QUALITY: int = 80
    MAX_DIM_PX: int = 1600
    STRIP_GPS: bool = True
    
    # Rate limiting
    RATE_LIMIT_GLOBAL: str = "60/minute"
    RATE_LIMIT_UPLOAD: str = "10/minute"
    
    # Safe Defaults & Bulk Processing
    SAFE_DEFAULTS: bool = True
    SINGLE_ITEM_DEFAULT_MAX_PHOTOS: int = 80
    
    # Clustering Configuration
    BULK_CLUSTER_EPS: float = 0.33
    BULK_MIN_SAMPLES: int = 2
    
    # Label Detection & Auto-Merge
    BULK_LABEL_SCORE_MIN: float = 0.55
    BULK_LABEL_ATTACH: bool = True
    BULK_MERGE_SINGLETONS: bool = True
    BULK_LABEL_MAX_PER_ITEM: int = 3


settings = Settings()
