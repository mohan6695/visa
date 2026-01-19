"""Configuration settings for Visa Q&A Backend
Uses centralized config from project root config/ module"""

import os
import sys
from pathlib import Path

# Add project root to path for centralized config
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings

# Re-export settings for backward compatibility
# These properties delegate to the centralized settings instance
class Settings:
    """Backward compatibility wrapper around centralized settings"""
    
    @property
    def SUPABASE_URL(self) -> str:
        return settings.supabase_url
    
    @property
    def SUPABASE_KEY(self) -> str:
        return settings.supabase_key
    
    @property
    def SUPABASE_ANON_KEY(self) -> str:
        return settings.supabase_anon_key
    
    @property
    def REDIS_URL(self) -> str:
        return settings.redis_url
    
    @property
    def REDIS_API_KEY(self) -> str:
        return settings.redis_api_key
    
    @property
    def AI_PROVIDER(self) -> str:
        return settings.ai_provider
    
    @property
    def GROQ_API_KEY(self) -> str:
        return settings.groq_api_key
    
    GROQ_MODEL = "llama-3.1-70b-versatile"
    
    @property
    def OPENROUTER_API_KEY(self) -> str:
        return settings.openrouter_api_key
    
    @property
    def STRIPE_SECRET_KEY(self) -> str:
        return settings.stripe_secret_key
    
    @property
    def STRIPE_WEBHOOK_SECRET(self) -> str:
        return settings.stripe_webhook_secret
    
    @property
    def POSTHOG_API_KEY(self) -> str:
        return settings.posthog_api_key
    
    @property
    def POSTHOG_HOST(self) -> str:
        return settings.posthog_host
    
    @property
    def ENABLE_HYBRID_ANALYTICS(self) -> bool:
        return settings.get_bool('ENABLE_HYBRID_ANALYTICS', False)
    
    @property
    def STORE_EVENTS_LOCALLY(self) -> bool:
        return settings.get_bool('STORE_EVENTS_LOCALLY', True)
    
    @property
    def OPENAI_API_KEY(self) -> str:
        return settings.openai_api_key
    
    EMBEDDING_MODEL = "text-embedding-3-small"
    
    @property
    def groq_api_key(self) -> str:
        return settings.groq_api_key
    
    groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    @property
    def APP_NAME(self) -> str:
        return settings.app_name
    
    @property
    def APP_VERSION(self) -> str:
        return settings.app_version
    
    @property
    def DEBUG(self) -> bool:
        return settings.debug
    
    @property
    def RATE_LIMIT_REQUESTS(self) -> int:
        return settings.get_int('RATE_LIMIT_REQUESTS', 100)
    
    @property
    def RATE_LIMIT_WINDOW(self) -> int:
        return settings.get_int('RATE_LIMIT_WINDOW', 60)
    
    @property
    def CACHE_TTL(self) -> int:
        return settings.get_int('CACHE_TTL', 7200)
    
    @property
    def CACHE_MAX_SIZE(self) -> int:
        return settings.get_int('CACHE_MAX_SIZE', 10000)
    
    @property
    def ENABLE_AUTO_TAGGING(self) -> bool:
        return settings.get_bool('ENABLE_AUTO_TAGGING', True)
    
    @property
    def ENABLE_EXTERNAL_PIPELINE(self) -> bool:
        return settings.get_bool('ENABLE_EXTERNAL_PIPELINE', True)
    
    @property
    def ENABLE_ANALYTICS(self) -> bool:
        return settings.get_bool('ENABLE_ANALYTICS', True)
    
    @property
    def AKISMET_API_KEY(self) -> str:
        return settings.akismet_api_key
    
    @property
    def AKISMET_BLOG_URL(self) -> str:
        return settings.get('AKISMET_BLOG_URL', 'https://your-domain.com')
    
    @property
    def AKISMET_ENABLED(self) -> bool:
        return settings.get_bool('AKISMET_ENABLED', True)


# Global settings instance for backward compatibility
settings = Settings()
