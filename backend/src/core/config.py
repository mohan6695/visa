"""
Core configuration for Visa Platform
Handles environment variables, database connections, and application settings
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "Visa Platform API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Visa Platform"
    
    # Security
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000"]
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # Supabase
    SUPABASE_URL: Optional[str] = Field(None, env="SUPABASE_URL")
    SUPABASE_ANON_KEY: Optional[str] = Field(None, env="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(None, env="SUPABASE_SERVICE_ROLE_KEY")
    
    # Redis
    REDIS_URL: str = Field(..., env="REDIS_URL")
    
    # Search Engine
    MEILI_MASTER_KEY: str = Field(default="masterKey", env="MEILI_MASTER_KEY")
    
    # AI/LLM Services
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    HUGGINGFACE_API_KEY: Optional[str] = Field(None, env="HUGGINGFACE_API_KEY")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["jpg", "jpeg", "png", "pdf", "doc", "docx"]
    
    # External Services
    STRIPE_SECRET_KEY: Optional[str] = Field(None, env="STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = Field(None, env="STRIPE_PUBLISHABLE_KEY")
    
    # Email
    SMTP_HOST: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: str = Field(..., env="SMTP_USER")
    SMTP_PASSWORD: str = Field(..., env="SMTP_PASSWORD")
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")
    PROMETHEUS_ENABLED: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    
    # Feature Flags
    ENABLE_AI_CHAT: bool = Field(default=True, env="ENABLE_AI_CHAT")
    ENABLE_REAL_TIME: bool = Field(default=True, env="ENABLE_REAL_TIME")
    ENABLE_NOTIFICATIONS: bool = Field(default=True, env="ENABLE_NOTIFICATIONS")
    ENABLE_ANALYTICS: bool = Field(default=True, env="ENABLE_ANALYTICS")
    
    # Performance
    CACHE_TTL: int = 3600  # 1 hour
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get application settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings