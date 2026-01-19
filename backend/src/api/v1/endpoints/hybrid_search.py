"""
Hybrid Search API Endpoints
StackOverflow-style sidebar posts with sub-200ms latency
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.src.api.v1.dependencies import get_current_user, get_supabase_client
from backend.src.services.hybrid_search_service import (
    HybridSearchService,
    create_hybrid_search_service,
    HybridSearchConfig
)
from backend.src.core.config import settings
from supabase import Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hybrid-search", tags=["hybrid-search"])

# Service instances (lazy initialization)
_services: dict = {}

def get_hybrid_search_service() -> HybridSearchService:
    """Get or create hybrid search service"""
    key = "default"
    if key not in _services:
        redis_url = getattr(settings, "REDIS_URL", None)
        _services[key] = create_hybrid_search_service(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY,
            redis_url=redis_url
        )
    return _services[key]


# Request/Response Models
class HybridSearchRequest(BaseModel):
    """Request model for hybrid search"""
    query: str
    group_id: str
    use_cache: bool = True
    cache_ttl: int = 3600
    include_sidebar: bool = True
    sidebar_limit: int = 12


class HybridSearchResponse(BaseModel):
    """Response model for hybrid search"""
    query: str
    main_answer: list
    sidebar_posts: list
    total_results: int
    latency_ms: float
    cache_hit: bool
    latency_breakdown: dict


class SidebarRequest(BaseModel):
    """Request model for sidebar posts"""
    group_id: str
    exclude_post_id: Optional[str] = None
    limit: int = 12


class SidebarResponse(BaseModel):
    """Response model for sidebar posts"""
    group_id: str
    posts: list
    count: int
    latency_ms: float


@router.post("/search", response_model=HybridSearchResponse)
async def hybrid_search(
    request: HybridSearchRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Perform hybrid search with RRF and FlashRank reranking
    
    Returns:
        - Main answer (top 3 results)
        - Sidebar posts (next 9 results)
    """
    service = get_hybrid_search_service()
    
    try:
        # Get query embedding
        from backend.src.services.embedding_service import get_embedding
        
        embedding_service = get_embedding()
        query_embedding = embedding_service.get_embedding(request.query)
        
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        # Perform hybrid search
        results, metadata = service.hybrid_search(
            query=request.query,
            query_embedding=query_embedding,
            group_id=request.group_id,
            use_cache=request.use_cache,
            cache_ttl=request.cache_ttl
        )
        
        # Split into main answer and sidebar
        main_answer = results[:3]
        sidebar_posts = results[3:12] if request.include_sidebar else []
        
        return HybridSearchResponse(
            query=request.query,
            main_answer=main_answer,
            sidebar_posts=sidebar_posts,
            total_results=metadata.get("total_results", 0),
            latency_ms=service.metrics.get("total_time", 0) * 1000,
            cache_hit=metadata.get("cache_hit", False),
            latency_breakdown=metadata.get("latency_breakdown", {})
        )
        
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sidebar", response_model=SidebarResponse)
async def get_sidebar_posts(
    request: SidebarRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get sidebar posts for a group (popular/trending)
    
    Used for:
    - Sidebar suggestions
    - Related posts
    - Trending content
    """
    service = get_hybrid_search_service()
    
    try:
        import time
        start = time.time()
        
        posts = service.get_sidebar_posts(
            group_id=request.group_id,
            exclude_post_id=request.exclude_post_id,
            limit=request.limit
        )
        
        latency_ms = (time.time() - start) * 1000
        
        return SidebarResponse(
            group_id=request.group_id,
            posts=posts,
            count=len(posts),
            latency_ms=latency_ms
        )
        
    except Exception as e:
        logger.error(f"Sidebar error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_search_metrics():
    """Get search service metrics"""
    service = get_hybrid_search_service()
    return service.get_metrics()


@router.post("/metrics/reset")
async def reset_metrics():
    """Reset search metrics"""
    service = get_hybrid_search_service()
    service.reset_metrics()
    return {"status": "ok"}


@router.get("/health")
async def health_check():
    """Health check for hybrid search service"""
    service = get_hybrid_search_service()
    
    return {
        "status": "healthy",
        "reranker_available": service.reranker.ranker is not None,
        "cache_available": service.redis is not None,
        "metrics": service.get_metrics()
    }
