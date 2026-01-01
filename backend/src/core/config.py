"""Configuration settings for Visa Q&A Backend"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # LLM - Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    
    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    
    # PostHog
    POSTHOG_API_KEY: str = os.getenv("POSTHOG_API_KEY", "")
    POSTHOG_HOST: str = os.getenv("POSTHOG_HOST", "https://app.posthog.com")
    
    # Hybrid Analytics Configuration
    ENABLE_HYBRID_ANALYTICS: bool = os.getenv("ENABLE_HYBRID_ANALYTICS", "false").lower() == "true"
    STORE_EVENTS_LOCALLY: bool = os.getenv("STORE_EVENTS_LOCALLY", "true").lower() == "true"
    
    # Embedding service
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Application settings
    APP_NAME: str = "Visa Q&A Chat"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Cache settings
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "7200"))  # 2 hours
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "10000"))
    
    # Feature flags
    ENABLE_AUTO_TAGGING: bool = os.getenv("ENABLE_AUTO_TAGGING", "true").lower() == "true"
    ENABLE_EXTERNAL_PIPELINE: bool = os.getenv("ENABLE_EXTERNAL_PIPELINE", "true").lower() == "true"
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()