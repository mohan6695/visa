"""
Sidebar API Endpoints

Provides StackOverflow-style sidebar with hybrid search:
- Main answer (top-3 posts)
- Sidebar (9+ related posts)
- Sub-100ms with cache hits
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from ...database import get_db
from ...services.hybrid_search_service import HybridSearchService
from ...services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sidebar", tags=["sidebar"])


@router.get("/search")
async def sidebar_search(
    q: str = Query(..., description="Search query for sidebar"),
    group_id: Optional[str] = Query(None, description="Filter by group ID"),
    limit: int = Query(12, ge=1, le=50, description="Number of posts to return"),
    use_rerank: bool = Query(True, description="Use FlashRank reranking"),
    use_cache: bool = Query(True, description="Use Redis cache"),
    db: Session = Depends(get_db)
):
    """
    Hybrid sidebar search with RRF and FlashRank reranking.
    
    Returns top posts for sidebar display with sub-100ms latency.
    
    Flow:
    1. L1 Cache check (1ms)
    2. Parallel semantic + keyword search (~100ms)
    3. RRF merge (~5ms)
    4. FlashRank rerank (~30ms)
    
    Returns: Main answer (top-3) + Sidebar posts (9+)
    """
    try:
        # Generate embedding for query
        embedding_service = EmbeddingService()
        query_embedding = await embedding_service.get_embedding(q)
        
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")
        
        # Perform hybrid search
        search_service = HybridSearchService(db)
        results = await search_service.hybrid_sidebar_search(
            query=q,
            query_embedding=query_embedding,
            group_id=group_id,
            limit=limit,
            use_rerank=use_rerank,
            use_cache=use_cache
        )
        
        # Split into main answer (top-3) and sidebar (rest)
        posts = results.get("posts", [])
        main_answer = posts[:3] if len(posts) >= 3 else posts
        sidebar_posts = posts[3:] if len(posts) > 3 else []
        
        return {
            "query": q,
            "main_answer": main_answer,
            "sidebar_posts": sidebar_posts,
            "total_posts": len(posts),
            "metadata": {
                "source": results.get("source"),
                "latency_ms": results.get("latency_ms"),
                "cached": results.get("cached"),
                "breakdown": results.get("breakdown")
            }
        }
        
    except Exception as e:
        logger.error(f"Sidebar search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot")
async def hot_sidebar_posts(
    group_id: str = Query(..., description="Group ID for hot posts"),
    limit: int = Query(10, ge=1, le=20, description="Number of posts to return"),
    db: Session = Depends(get_db)
):
    """
    Get hot/trending posts for sidebar.
    
    Fast, cached endpoint for trending content.
    """
    try:
        search_service = HybridSearchService(db)
        posts = await search_service.get_hot_sidebar_posts(
            group_id=group_id,
            limit=limit
        )
        
        return {
            "posts": posts,
            "count": len(posts),
            "type": "hot"
        }
        
    except Exception as e:
        logger.error(f"Hot sidebar error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{post_id}")
async def similar_posts(
    post_id: str = Query(..., description="Post ID to find similar posts for"),
    limit: int = Query(5, ge=1, le=20, description="Number of similar posts"),
    db: Session = Depends(get_db)
):
    """
    Get similar posts based on semantic similarity.
    
    Used for 'Related in group' sidebar section.
    """
    try:
        search_service = HybridSearchService(db)
        posts = await search_service.get_similar_posts(
            post_id=post_id,
            limit=limit
        )
        
        return {
            "post_id": post_id,
            "similar_posts": posts,
            "count": len(posts),
            "type": "similar"
        }
        
    except Exception as e:
        logger.error(f"Similar posts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk")
async def bulk_sidebar_queries(
    queries: List[dict],
    db: Session = Depends(get_db)
):
    """
    Batch sidebar queries for multiple searches.
    
    Useful for preloading sidebar content.
    """
    try:
        results = []
        embedding_service = EmbeddingService()
        search_service = HybridSearchService(db)
        
        for query_item in queries:
            q = query_item.get("query")
            group_id = query_item.get("group_id")
            limit = query_item.get("limit", 12)
            
            if not q:
                continue
            
            # Generate embedding
            query_embedding = await embedding_service.get_embedding(q)
            if not query_embedding:
                continue
            
            # Search
            search_results = await search_service.hybrid_sidebar_search(
                query=q,
                query_embedding=query_embedding,
                group_id=group_id,
                limit=limit
            )
            
            results.append({
                "query": q,
                "posts": search_results.get("posts", []),
                "latency_ms": search_results.get("latency_ms")
            })
        
        return {
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Bulk sidebar error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
