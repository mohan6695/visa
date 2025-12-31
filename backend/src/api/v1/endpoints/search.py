from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from ..dependencies import get_db, get_current_user
from ...services.search_service import SearchService
from ...models.user import User
from ...core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/search/posts")
async def search_posts(
    query: str = Query(..., min_length=2, max_length=100),
    country: str = Query(..., description="Country code (usa, canada, uk, australia)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search posts with full-text search and filtering"""
    try:
        search_service = SearchService(db)
        result = await search_service.search_posts(query, country, limit, offset)
        
        return {
            "success": True,
            "data": result,
            "query": query,
            "country": country
        }
        
    except Exception as e:
        logger.error(f"Search posts API error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/search/comments")
async def search_comments(
    query: str = Query(..., min_length=2, max_length=100),
    post_id: Optional[int] = Query(None, description="Filter comments by post ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search comments with full-text search"""
    try:
        search_service = SearchService(db)
        result = await search_service.search_comments(query, post_id, limit, offset)
        
        return {
            "success": True,
            "data": result,
            "query": query,
            "post_id": post_id
        }
        
    except Exception as e:
        logger.error(f"Search comments API error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/search/communities")
async def search_communities(
    query: str = Query(..., min_length=2, max_length=100),
    country: str = Query(..., description="Country code (usa, canada, uk, australia)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search communities with full-text search"""
    try:
        search_service = SearchService(db)
        result = await search_service.search_communities(query, country, limit, offset)
        
        return {
            "success": True,
            "data": result,
            "query": query,
            "country": country
        }
        
    except Exception as e:
        logger.error(f"Search communities API error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/search/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=2, max_length=50),
    country: str = Query(..., description="Country code (usa, canada, uk, australia)"),
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get search suggestions based on popular queries and content"""
    try:
        search_service = SearchService(db)
        suggestions = await search_service.get_search_suggestions(query, country, limit)
        
        return {
            "success": True,
            "data": {
                "suggestions": suggestions,
                "query": query,
                "country": country
            }
        }
        
    except Exception as e:
        logger.error(f"Get search suggestions API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")

@router.get("/search/trending")
async def get_trending_topics(
    country: str = Query(..., description="Country code (usa, canada, uk, australia)"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trending topics based on recent activity"""
    try:
        search_service = SearchService(db)
        topics = await search_service.get_trending_topics(country, limit)
        
        return {
            "success": True,
            "data": {
                "topics": topics,
                "country": country,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Get trending topics API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trending topics")

@router.get("/search/advanced")
async def advanced_search(
    query: str = Query(..., min_length=2, max_length=100),
    country: str = Query(..., description="Country code (usa, canada, uk, australia)"),
    search_type: str = Query("all", regex="^(all|posts|comments|communities)$"),
    time_range: str = Query("week", regex="^(day|week|month|year|all)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Advanced search across multiple content types with filtering"""
    try:
        search_service = SearchService(db)
        results = {}
        
        if search_type in ["all", "posts"]:
            posts_result = await search_service.search_posts(query, country, limit, offset)
            results["posts"] = posts_result
            
        if search_type in ["all", "comments"]:
            comments_result = await search_service.search_comments(query, None, limit, offset)
            results["comments"] = comments_result
            
        if search_type in ["all", "communities"]:
            communities_result = await search_service.search_communities(query, country, limit, offset)
            results["communities"] = communities_result

        # Get trending topics as additional context
        trending_topics = await search_service.get_trending_topics(country, 5)
        
        return {
            "success": True,
            "data": {
                "results": results,
                "trending_topics": trending_topics,
                "query": query,
                "country": country,
                "search_type": search_type,
                "time_range": time_range
            }
        }
        
    except Exception as e:
        logger.error(f"Advanced search API error: {e}")
        raise HTTPException(status_code=500, detail="Advanced search failed")

@router.post("/search/index")
async def reindex_search_data(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reindex search data for better performance (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Add background task to reindex data
        background_tasks.add_task(_reindex_search_data, db)
        
        return {
            "success": True,
            "message": "Search data reindexing started in background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reindex search data API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start reindexing")

async def _reindex_search_data(db: Session):
    """Background task to reindex search data"""
    try:
        # Update full-text search vectors
        db.execute("""
            UPDATE posts 
            SET search_vector = to_tsvector('english', title || ' ' || content)
            WHERE search_vector IS NULL OR updated_at > created_at
        """)
        
        db.execute("""
            UPDATE comments 
            SET search_vector = to_tsvector('english', content)
            WHERE search_vector IS NULL OR updated_at > created_at
        """)
        
        db.execute("""
            UPDATE communities 
            SET search_vector = to_tsvector('english', name || ' ' || description)
            WHERE search_vector IS NULL OR updated_at > created_at
        """)
        
        db.commit()
        logger.info("Search data reindexing completed successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Search data reindexing failed: {e}")