from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Visa Community Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = Field(default="postgresql://postgres:password@localhost:5432/visa_community")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # API
    API_V1_STR: str = "/api/v1"
    
    # External APIs
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "visa-community-platform"
    
    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    
    # Redis (for caching and real-time features)
    REDIS_URL: Optional[str] = None
    REDIS_API_KEY: Optional[str] = None
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_SSL: bool = False
    
    # Email (for notifications)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "text/plain", "application/pdf"]
    
    # Search
    SEARCH_RESULTS_LIMIT: int = 100
    SEARCH_SUGGESTIONS_LIMIT: int = 10
    
    # Chat
    CHAT_MESSAGE_LIMIT: int = 1000
    CHAT_HISTORY_LIMIT: int = 50
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    # AI Configuration
    AI_PROVIDER: str = "groq"  # Options: groq, openrouter, ollama
    GROQ_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OLLAMA_URL: str = "http://localhost:11434"
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = False
    GRAFANA_ENABLED: bool = False
    
    # Development
    HOT_RELOAD: bool = True
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
        # Custom validation for required fields in production
        @classmethod
        def validate_production(cls, values):
            if values.get("ENVIRONMENT") == "production":
                required_fields = ["SECRET_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
                for field in required_fields:
                    if not values.get(field):
                        raise ValueError(f"{field} is required in production")
            return values

# Telegram Upload Configuration
class TelegramUploadConfig:
    """Configuration for Telegram chat upload service"""
    
    # Processing settings
    BATCH_SIZE: int = 1000  # Optimal batch size for bulk inserts
    MAX_CONCURRENT_UPLOADS: int = 5  # Limit concurrent operations
    CHUNK_SIZE: int = 50000  # For streaming large files
    
    # Date filtering
    RECENT_DAYS_THRESHOLD: int = 30  # Messages from last 30 days go to database
    
    # Message processing
    MAX_TEXT_CONTENT_LENGTH: int = 10000  # Limit text content size
    ALIAS_LENGTH: int = 8  # Length of generated user aliases
    
    # Storage settings
    STORAGE_BUCKET: str = "telegram-archives"
    SUMMARY_FILE_PREFIX: str = "summary_before"
    
    # Performance settings
    BATCH_DELAY_SECONDS: float = 0.1  # Delay between batches
    POSTGREST_TIMEOUT: int = 60  # 60 seconds timeout for bulk operations
    STORAGE_TIMEOUT: int = 120  # 2 minutes for large file uploads

settings = Settings()
telegram_config = TelegramUploadConfig()