from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "Wardrobe Auto"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # External APIs (to be configured later)
    OPENWEATHER_API_KEY: Optional[str] = None
    GOOGLE_CALENDAR_CLIENT_ID: Optional[str] = None
    GOOGLE_CALENDAR_CLIENT_SECRET: Optional[str] = None
    RAKUTEN_APP_ID: Optional[str] = None
    RAKUTEN_AFFILIATE_ID: Optional[str] = None

    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
