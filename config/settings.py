# config/settings.py
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
import secrets

# Load environment variables
load_dotenv()

# Check Pydantic version to use the right approach
import pydantic
from packaging import version
PYDANTIC_V2 = version.parse(pydantic.__version__) >= version.parse("2.0.0")

if PYDANTIC_V2:
    # For Pydantic v2
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import field_validator
else:
    # For Pydantic v1
    from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Influencer Marketing Platform"
    API_V0_STR: str = "/api/v0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Instagram URL
    INSTAGRAM_URL: str = os.getenv("INSTAGRAM_BASE_URL", "https://www.instagram.com")

    # Instagram Credentials
    INSTAGRAM_USERNAME: Optional[str] = os.getenv("INSTAGRAM_USERNAME")
    INSTAGRAM_PASSWORD: Optional[str] = os.getenv("INSTAGRAM_PASSWORD")

    # Session Storage Path
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))  # Root directory
    SESSION_STORAGE_DIR: str = os.path.join(BASE_DIR, "../storage/sessions/instagram")  # Storage folder
    SESSION_STORAGE_PATH: str = os.path.join(SESSION_STORAGE_DIR, "instagram_session.json")  # JSON File

    # Playwright headless mode, true/false
    HEADLESS_MODE: bool = False

    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    ALGORITHM: str = "HS256"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = os.getenv(
        "BACKEND_CORS_ORIGINS", 
        "http://localhost,http://localhost:3000,http://localhost:3001,https://dashboard.echooo.ai,http://35.244.31.63:3000,http://192.168.18.74:3000"
    ).split(",")
    
    # Database settings
    DB_TYPE: str = os.getenv("DB_TYPE", "postgresql")
    DB_USERNAME: str = os.getenv("DB_USERNAME", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "echooo123")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "echooo_development_002")
    
    # Email settings
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "True").lower() == "true"
    SMTP_PORT: Optional[int] = int(os.getenv("SMTP_PORT", "587"))
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: Optional[str] = os.getenv("EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: Optional[str] = os.getenv("EMAILS_FROM_NAME")
    
    # File storage settings
    UPLOAD_DIRECTORY: str = os.getenv("UPLOAD_DIRECTORY", "uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "5242880"))  # 5MB
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD_SECONDS: int = int(os.getenv("RATE_LIMIT_PERIOD_SECONDS", "3600"))
    
    # For Pydantic v2
    if PYDANTIC_V2:
        model_config = SettingsConfigDict(
            case_sensitive=True,
            env_file=".env",
            extra="ignore"  # Allow extra fields in the environment
        )
    else:
        class Config:
            case_sensitive = True
            env_file = ".env"
            extra = "ignore"  # Allow extra fields in the environment

    # Define database URL property
    @property
    def DATABASE_URL(self) -> str:
        """
        Assemble the database URL from components
        """
        return f"{self.DB_TYPE}://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Define the validator based on Pydantic version
    if PYDANTIC_V2:
        @field_validator('BACKEND_CORS_ORIGINS')
        @classmethod
        def assemble_cors_origins(cls, v):
            if isinstance(v, str) and not v.startswith("["):
                return [i.strip() for i in v.split(",")]
            if isinstance(v, (list, str)):
                return v
            raise ValueError(v)
    else:
        @validator("BACKEND_CORS_ORIGINS", pre=True)
        def assemble_cors_origins(cls, v):
            if isinstance(v, str) and not v.startswith("["):
                return [i.strip() for i in v.split(",")]
            if isinstance(v, (list, str)):
                return v
            raise ValueError(v)

# Create settings instance
settings = Settings()