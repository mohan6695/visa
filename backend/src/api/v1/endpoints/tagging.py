from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel, Field
import logging
from supabase import Client
from ....services.auto_tagging_service import AutoTaggingService
from ....services.optimized_ai_service import OptimizedAIService
from ....services.embedding_service import EmbeddingService
from ....services.supabase_auth_service import SupabaseAuthService, get_auth_service
from ....core.redis import get_redis
from ....core.config import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tagging", tags=["Tagging"])

# Pydantic models for request validation
class TagPostRequest(BaseModel):
    post_id: str
    content: str
    title: Optional[str] = None

class ClusterRequest(BaseModel):
    limit: int = Field(100, ge=1, le=500)

class TagResponse(BaseModel):
    post_id: str
    tags: List[str]
    success: bool

class ClusterResponse(BaseModel):
    status: str
    message: str
    clusters: int
    posts_processed: Optional[int] = None

# Dependency to get AutoTaggingService
async def get_auto_tagging_service(
    supabase: Client = Depends(get_supabase_client),
    ai_service: OptimizedAIService = Depends(lambda: OptimizedAIService(
        redis_client=get_redis(),
        embedding_service=EmbeddingService()
    ))
) -> AutoTaggingService:
    return AutoTaggingService(
        supabase_client=supabase,
        ai_service=ai_service,
        embedding_service=EmbeddingService()
    )

@router.post("/tag-post", response_model=TagResponse)
async def tag_post(
    request_data: TagPostRequest,
    background_tasks: BackgroundTasks,
    auto_tagging_service: AutoTaggingService = Depends(get_auto_tagging_service),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Automatically tag a post using LLM and similarity-based approaches
    """
    try:
        # Run tagging in background to not block the request
        background_tasks.add_task(
            auto_tagging_service.auto_tag_post,
            post_id=request_data.post_id,
            content=request_data.content,
            title=request_data.title
        )
        
        return {
            "post_id": request_data.post_id,
            "tags": [],  # Tags will be applied asynchronously
            "success": True
        }
    except Exception as e:
        logger.error(f"Error tagging post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to tag post: {str(e)}"
        )

@router.post("/cluster-posts", response_model=ClusterResponse)
async def cluster_posts(
    request_data: ClusterRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    auto_tagging_service: AutoTaggingService = Depends(get_auto_tagging_service),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Cluster similar posts for content organization
    """
    try:
        # Check if user is admin
        user = request.state.user
        if user.get("role") not in ["admin", "service_role"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Run clustering in background
        background_tasks.add_task(
            auto_tagging_service.cluster_similar_posts,
            limit=request_data.limit
        )
        
        return {
            "status": "success",
            "message": f"Clustering started for up to {request_data.limit} posts",
            "clusters": 0  # Will be updated by background task
        }
    except Exception as e:
        logger.error(f"Error clustering posts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cluster posts: {str(e)}"
        )

@router.post("/process-external-content", response_model=ClusterResponse)
async def process_external_content(
    request: Request,
    background_tasks: BackgroundTasks,
    auto_tagging_service: AutoTaggingService = Depends(get_auto_tagging_service),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Process external content from staging to live
    """
    try:
        # Check if user is admin
        user = request.state.user
        if user.get("role") not in ["admin", "service_role"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Run processing in background
        background_tasks.add_task(
            auto_tagging_service.process_external_content
        )
        
        return {
            "status": "success",
            "message": "External content processing started",
            "clusters": 0  # Will be updated by background task
        }
    except Exception as e:
        logger.error(f"Error processing external content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process external content: {str(e)}"
        )