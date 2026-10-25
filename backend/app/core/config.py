import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Healthcare Predictive Analytics System"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Robust path: ensures identical DB file regardless of cwd
    _default_db_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "healthcare.db"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{_default_db_path}")
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # Model storage paths
    MODELS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

    # Email / Notification SMTP Settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@smarthealth.local"
    ENABLE_SCHEDULER: bool = True

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or len(v.strip()) < 32:
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: SECRET_KEY is missing or shorter than 32 characters. "
                "Set a secure SECRET_KEY in your environment or .env file using `python scripts/generate_secret.py`."
            )
        return v

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()

