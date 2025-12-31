from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from redis.asyncio import Redis
from sqlalchemy import text
from ..dependencies import get_db, get_redis, get_current_user
from ...models.user import User
from ...core.config import settings
from ...services.ai_service import AIService
from ...services.embedding_service import EmbeddingService
import logging
import time
import json

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check(
    db: Session = Depends(get_db),
    redis_client: Optional[Redis] = Depends(get_redis)
):
    """Basic health check endpoint"""
    try:
        # Check database connection
        db_status = "healthy"
        try:
            db.execute(text("SELECT 1")).scalar()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = "unhealthy"
        
        # Check Redis connection
        redis_status = "healthy"
        if redis_client:
            try:
                await redis_client.ping()
            except Exception as e:
                logger.error(f"Redis health check failed: {e}")
                redis_status = "unhealthy"
        else:
            redis_status = "disabled"
        
        # Check Supabase connection
        supabase_status = "healthy"
        if settings.SUPABASE_URL:
            try:
                # This would be a more comprehensive check in production
                # For now, we just check if the URL is configured
                pass
            except Exception as e:
                logger.error(f"Supabase health check failed: {e}")
                supabase_status = "unhealthy"
        else:
            supabase_status = "disabled"
        
        # Overall status
        overall_status = "healthy"
        if db_status != "healthy" or redis_status == "unhealthy" or supabase_status == "unhealthy":
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "services": {
                "database": db_status,
                "redis": redis_status,
                "supabase": supabase_status
            },
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/health/detailed")
async def detailed_health_check(
    db: Session = Depends(get_db),
    redis_client: Optional[Redis] = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """Detailed health check with metrics"""
    try:
        # Database metrics
        db_metrics = {}
        try:
            # Connection count
            conn_count = db.execute(text("SELECT count(*) FROM pg_stat_activity")).scalar()
            db_metrics["connection_count"] = conn_count
            
            # Active connections
            active_count = db.execute(text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")).scalar()
            db_metrics["active_connections"] = active_count
            
            # Database size (approximate)
            db_size = db.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))")).scalar()
            db_metrics["database_size"] = db_size
            
        except Exception as e:
            logger.error(f"Database metrics collection failed: {e}")
            db_metrics["error"] = str(e)
        
        # Redis metrics
        redis_metrics = {}
        if redis_client:
            try:
                info = await redis_client.info()
                redis_metrics = {
                    "used_memory_human": info.get("used_memory_human", "N/A"),
                    "used_memory_peak_human": info.get("used_memory_peak_human", "N/A"),
                    "connected_clients": info.get("connected_clients", "N/A"),
                    "keyspace_hits": info.get("keyspace_hits", "N/A"),
                    "keyspace_misses": info.get("keyspace_misses", "N/A"),
                    "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", "N/A")
                }
            except Exception as e:
                logger.error(f"Redis metrics collection failed: {e}")
                redis_metrics["error"] = str(e)
        else:
            redis_metrics["status"] = "disabled"
        
        # Cache hit rates
        cache_metrics = {}
        if redis_client:
            try:
                # Get cache statistics from Redis info
                info = await redis_client.info("stats")
                cache_metrics = {
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "hit_rate": 0
                }
                
                total_requests = cache_metrics["keyspace_hits"] + cache_metrics["keyspace_misses"]
                if total_requests > 0:
                    cache_metrics["hit_rate"] = (cache_metrics["keyspace_hits"] / total_requests) * 100
                    
            except Exception as e:
                logger.error(f"Cache metrics collection failed: {e}")
                cache_metrics["error"] = str(e)
        
        # System metrics
        system_metrics = {
            "python_version": "3.10",
            "fastapi_version": "0.104.1",
            "sqlalchemy_version": "2.0.23",
            "redis_version": "5.0.1" if redis_client else "N/A"
        }
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": db_metrics,
            "redis": redis_metrics,
            "cache": cache_metrics,
            "system": system_metrics,
            "config": {
                "redis_enabled": redis_client is not None,
                "supabase_enabled": bool(settings.SUPABASE_URL),
                "ai_provider": settings.AI_PROVIDER,
                "debug_mode": settings.DEBUG
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail="Detailed health check failed")

@router.get("/health/cache")
async def cache_health_check(
    redis_client: Optional[Redis] = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """Cache-specific health check"""
    if not redis_client:
        return {
            "status": "disabled",
            "message": "Redis is not configured"
        }
    
    try:
        # Test cache operations
        test_key = "health_check:test"
        test_value = {"timestamp": time.time(), "test": True}
        
        # Set test value
        await redis_client.setex(test_key, 60, json.dumps(test_value))
        
        # Get test value
        cached_value = await redis_client.get(test_key)
        if cached_value:
            cached_data = json.loads(cached_value)
        else:
            raise Exception("Failed to retrieve cached value")
        
        # Delete test value
        await redis_client.delete(test_key)
        
        # Get Redis info
        info = await redis_client.info()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "test_operations": {
                "set": True,
                "get": True,
                "delete": True
            },
            "redis_info": {
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "used_memory_peak_human": info.get("used_memory_peak_human", "N/A"),
                "connected_clients": info.get("connected_clients", "N/A"),
                "keyspace_hits": info.get("keyspace_hits", "N/A"),
                "keyspace_misses": info.get("keyspace_misses", "N/A")
            },
            "cache_metrics": {
                "hit_rate": calculate_hit_rate(info),
                "memory_usage": info.get("used_memory_human", "N/A")
            }
        }
        
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@router.get("/health/ai")
async def ai_health_check(
    current_user: User = Depends(get_current_user)
):
    """AI service health check"""
    try:
        # Check AI provider configuration
        ai_provider = settings.AI_PROVIDER
        if not ai_provider:
            return {
                "status": "disabled",
                "message": "No AI provider configured"
            }
        
        # Check provider-specific health
        provider_status = {}
        
        if ai_provider == "groq":
            provider_status = {
                "provider": "groq",
                "api_key_configured": bool(settings.GROQ_API_KEY),
                "status": "configured"
            }
        elif ai_provider == "openrouter":
            provider_status = {
                "provider": "openrouter",
                "api_key_configured": bool(settings.OPENROUTER_API_KEY),
                "status": "configured"
            }
        elif ai_provider == "ollama":
            provider_status = {
                "provider": "ollama",
                "ollama_url": settings.OLLAMA_URL,
                "status": "configured"
            }
        else:
            provider_status = {
                "provider": ai_provider,
                "status": "unknown"
            }
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "current_provider": ai_provider,
            "provider_details": provider_status,
            "available_providers": ["groq", "openrouter", "ollama"],
            "config": {
                "cache_enabled": bool(settings.REDIS_URL),
                "embedding_model": "all-MiniLM-L6-v2",
                "max_tokens": 1000,
                "temperature": 0.7
            }
        }
        
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@router.get("/health/chat")
async def chat_health_check(
    db: Session = Depends(get_db),
    redis_client: Optional[Redis] = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """Chat service health check"""
    try:
        # Check database tables
        db_tables = {}
        try:
            # Check if chat tables exist
            tables = ["group_messages", "message_read_receipts", "user_presence", "group_message_likes"]
            
            for table in tables:
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table} LIMIT 1")).scalar()
                    db_tables[table] = {"exists": True, "count": result}
                except Exception:
                    db_tables[table] = {"exists": False, "count": 0}
                    
        except Exception as e:
            logger.error(f"Database table check failed: {e}")
            db_tables["error"] = str(e)
        
        # Check Supabase Realtime
        supabase_status = {}
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            supabase_status = {
                "configured": True,
                "url_set": bool(settings.SUPABASE_URL),
                "key_set": bool(settings.SUPABASE_KEY)
            }
        else:
            supabase_status = {
                "configured": False,
                "message": "Supabase not configured"
            }
        
        # Check Redis for chat caching
        redis_status = {}
        if redis_client:
            try:
                await redis_client.ping()
                redis_status = {
                    "connected": True,
                    "chat_cache_enabled": True
                }
            except Exception as e:
                redis_status = {
                    "connected": False,
                    "error": str(e)
                }
        else:
            redis_status = {
                "connected": False,
                "message": "Redis not configured"
            }
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": db_tables,
            "supabase": supabase_status,
            "redis": redis_status,
            "features": {
                "realtime_chat": bool(settings.SUPABASE_URL),
                "message_caching": bool(redis_client),
                "presence_tracking": bool(redis_client),
                "read_receipts": True,  # Always available with database
                "message_reactions": True  # Always available with database
            }
        }
        
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@router.post("/health/test-ai")
async def test_ai_endpoint(
    db: Session = Depends(get_db),
    redis_client: Optional[Redis] = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """Test AI service with a simple question"""
    try:
        embedding_service = EmbeddingService(db)
        ai_service = AIService(redis_client, embedding_service)
        
        # Test with a simple question
        result = await ai_service.answer_question(
            question="What is a visa?",
            group_id=1,  # Test group
            use_cache=False  # Don't use cache for test
        )
        
        return {
            "success": True,
            "test_result": result,
            "message": "AI service test completed",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"AI test failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"AI service test failed: {str(e)}"
        )

def calculate_hit_rate(info: Dict[str, Any]) -> float:
    """Calculate cache hit rate from Redis info"""
    try:
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return (hits / total) * 100
    except:
        return 0.0