"""
Centralized Settings for Visa Community Platform
Loads configuration from YAML files and environment variables
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class Settings:
    """Centralized settings class that loads from YAML and environment variables"""
    
    _instance: Optional['Settings'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls) -> 'Settings':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self) -> None:
        """Load configuration from YAML files"""
        config_path = Path(__file__).parent
        
        # Load project config
        project_config_path = config_path / "project_config.yaml"
        if project_config_path.exists():
            with open(project_config_path, 'r') as f:
                self._config.update(yaml.safe_load(f) or {})
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value from YAML or environment variables"""
        # First check environment variables (takes precedence)
        env_value = os.getenv(key.upper())
        if env_value is not None:
            return env_value
        
        # Check nested config with dot notation
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean configuration value"""
        value = self.get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return default
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer configuration value"""
        value = self.get(key)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get a float configuration value"""
        value = self.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return default
        return default
    
    @property
    def supabase_url(self) -> str:
        return self.get('SUPABASE_URL', '')
    
    @property
    def supabase_key(self) -> str:
        return self.get('SUPABASE_KEY', '')
    
    @property
    def supabase_anon_key(self) -> str:
        return self.get('SUPABASE_ANON_KEY', '')
    
    @property
    def redis_url(self) -> str:
        return self.get('REDIS_URL', 'redis://localhost:6379')
    
    @property
    def redis_api_key(self) -> str:
        return self.get('REDIS_API_KEY', '')
    
    @property
    def ai_provider(self) -> str:
        return self.get('AI_PROVIDER', 'groq')
    
    @property
    def groq_api_key(self) -> str:
        return self.get('GROQ_API_KEY', '')
    
    @property
    def openrouter_api_key(self) -> str:
        return self.get('OPENROUTER_API_KEY', '')
    
    @property
    def ollama_url(self) -> str:
        return self.get('OLLAMA_URL', 'http://localhost:11434')
    
    @property
    def ollama_model(self) -> str:
        return self.get('OLLAMA_MODEL', 'qwen2.5:3b')
    
    @property
    def ollama_embedding_model(self) -> str:
        return self.get('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text')
    
    @property
    def ollama_embedding_dimensions(self) -> int:
        return self.get_int('OLLAMA_EMBEDDING_DIMENSIONS', 768)
    
    @property
    def ollama_enabled(self) -> bool:
        return self.get_bool('OLLAMA_ENABLED', True)
    
    @property
    def embedding_batch_size(self) -> int:
        return self.get_int('EMBEDDING_BATCH_SIZE', 10)
    
    @property
    def openai_api_key(self) -> str:
        return self.get('OPENAI_API_KEY', '')
    
    @property
    def posthog_api_key(self) -> str:
        return self.get('POSTHOG_API_KEY', '')
    
    @property
    def posthog_host(self) -> str:
        return self.get('POSTHOG_HOST', 'https://app.posthog.com')
    
    @property
    def stripe_secret_key(self) -> str:
        return self.get('STRIPE_SECRET_KEY', '')
    
    @property
    def stripe_webhook_secret(self) -> str:
        return self.get('STRIPE_WEBHOOK_SECRET', '')
    
    @property
    def akismet_api_key(self) -> str:
        return self.get('AKISMET_API_KEY', '')
    
    @property
    def debug(self) -> bool:
        return self.get_bool('DEBUG', False)
    
    @property
    def app_name(self) -> str:
        return self.get('APP_NAME', 'Visa Community Platform')
    
    @property
    def app_version(self) -> str:
        return self.get('APP_VERSION', '1.0.0')


# Global settings instance
settings = Settings()
