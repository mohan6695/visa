from typing import Optional
from redis.asyncio import Redis
from ..core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis connection manager for caching and real-time features"""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
    
    async def connect(self):
        """Initialize Redis connection"""
        try:
            if not settings.REDIS_URL and not settings.REDIS_HOST:
                logger.warning("Redis URL or host not configured, skipping Redis initialization")
                return
            
            # Build Redis URL based on configuration
            if settings.REDIS_URL:
                # Use direct URL if provided
                redis_url = settings.REDIS_URL
            else:
                # Build URL from individual components
                protocol = "rediss" if settings.REDIS_SSL else "redis"
                password_part = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
                redis_url = f"{protocol}://{password_part}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
            
            self.redis_client = Redis.from_url(
                redis_url,
                decode_responses=True,
                encoding="utf-8"
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    def get_client(self) -> Optional[Redis]:
        """Get Redis client instance"""
        return self.redis_client

# Global Redis manager instance
redis_manager = RedisManager()

async def get_redis() -> Optional[Redis]:
    """Dependency to get Redis client"""
    return redis_manager.get_client()

# Cache utility functions
class CacheService:
    """Utility class for common caching operations"""
    
    @staticmethod
    async def set_cache(
        redis_client: Redis,
        key: str,
        value: dict,
        ttl: int = 3600
    ) -> bool:
        """Set cache with TTL"""
        try:
            await redis_client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False
    
    @staticmethod
    async def get_cache(
        redis_client: Redis,
        key: str
    ) -> Optional[dict]:
        """Get cached value"""
        try:
            cached_data = await redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cache: {e}")
            return None
    
    @staticmethod
    async def delete_cache(
        redis_client: Redis,
        key: str
    ) -> bool:
        """Delete cached value"""
        try:
            await redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
            return False
    
    @staticmethod
    async def cache_exists(
        redis_client: Redis,
        key: str
    ) -> bool:
        """Check if cache exists"""
        try:
            return await redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check cache existence: {e}")
            return False
    
    @staticmethod
    async def get_cache_ttl(
        redis_client: Redis,
        key: str
    ) -> int:
        """Get cache TTL in seconds"""
        try:
            return await redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get cache TTL: {e}")
            return -1

# Specific cache operations for chat and AI
class ChatCacheService:
    """Cache operations specific to chat functionality"""
    
    @staticmethod
    def generate_message_cache_key(group_id: int, message_id: int) -> str:
        """Generate cache key for message"""
        return f"message:{group_id}:{message_id}"
    
    @staticmethod
    def generate_group_history_cache_key(group_id: int, limit: int, offset: int) -> str:
        """Generate cache key for group message history"""
        return f"group_history:{group_id}:{limit}:{offset}"
    
    @staticmethod
    def generate_presence_cache_key(group_id: int) -> str:
        """Generate cache key for group presence"""
        return f"presence:{group_id}"
    
    @staticmethod
    def generate_read_receipts_cache_key(user_id: int, group_id: int) -> str:
        """Generate cache key for read receipts"""
        return f"read_receipts:{user_id}:{group_id}"

class AICacheService:
    """Cache operations specific to AI functionality"""
    
    @staticmethod
    def generate_qa_cache_key(group_id: int, question: str, context_type: str = "full") -> str:
        """Generate cache key for Q&A"""
        import hashlib
        normalized_question = question.lower().strip()
        cache_input = f"{group_id}:{normalized_question}:{context_type}"
        return f"qa:{hashlib.md5(cache_input.encode()).hexdigest()}"
    
    @staticmethod
    def generate_search_cache_key(group_id: int, query: str, limit: int) -> str:
        """Generate cache key for search results"""
        import hashlib
        cache_input = f"{group_id}:{query}:{limit}"
        return f"search:{hashlib.md5(cache_input.encode()).hexdigest()}"
    
    @staticmethod
    def generate_summary_cache_key(group_id: int, thread_id: str, summary_type: str) -> str:
        """Generate cache key for thread summaries"""
        import hashlib
        cache_input = f"{group_id}:{thread_id}:{summary_type}"
        return f"summary:{hashlib.md5(cache_input.encode()).hexdigest()}"

# Rate limiting utilities
class RateLimitService:
    """Rate limiting using Redis"""
    
    @staticmethod
    async def is_rate_limited(
        redis_client: Redis,
        key: str,
        limit: int,
        window_seconds: int
    ) -> bool:
        """Check if request is rate limited"""
        try:
            current = await redis_client.get(key)
            if current is None:
                # First request in window
                await redis_client.setex(key, window_seconds, 1)
                return False
            
            current_count = int(current)
            if current_count >= limit:
                return True
            
            # Increment counter
            await redis_client.incr(key)
            return False
            
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return False
    
    @staticmethod
    def generate_rate_limit_key(user_id: int, endpoint: str) -> str:
        """Generate rate limit key"""
        return f"rate_limit:{user_id}:{endpoint}"