from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel, Field
import logging
from redis.asyncio import Redis
from ....services.optimized_ai_service import OptimizedAIService
from ....services.embedding_service import EmbeddingService
from ....services.supabase_auth_service import SupabaseAuthService, get_auth_service
from ....core.redis import get_redis
from ....core.config import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])

# Pydantic models for request validation
class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)
    group_id: str
    community_id: Optional[str] = None
    use_cache: bool = True
    context_type: str = "full"

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)
    group_id: str
    community_id: Optional[str] = None
    limit: int = Field(10, ge=1, le=50)
    threshold: float = Field(0.7, ge=0.0, le=1.0)

class Source(BaseModel):
    type: str
    id: str
    content: str
    created_at: Optional[str] = None
    similarity: Optional[float] = None

class Metrics(BaseModel):
    latency: float
    cache_hit: bool
    model: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    error: Optional[str] = None

class AnswerResponse(BaseModel):
    answer: str
    source: str
    timestamp: Optional[str] = None
    sources: List[Source] = []
    metrics: Optional[Metrics] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    count: int
    query: str
    metrics: Optional[Dict[str, Any]] = None

# Dependency to get AI service
async def get_ai_service(
    redis: Redis = Depends(get_redis),
    embedding_service: EmbeddingService = Depends(lambda: EmbeddingService())
) -> OptimizedAIService:
    return OptimizedAIService(redis, embedding_service)

@router.post("/answer", response_model=AnswerResponse)
async def answer_question(
    request_data: QuestionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    ai_service: OptimizedAIService = Depends(get_ai_service),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Answer a question using AI with RAG (Retrieval Augmented Generation)
    """
    try:
        # Get user from request state
        user = request.state.user
        is_premium = request.state.is_premium
        
        # Validate group access
        if not await auth_service.verify_group_access(request_data.group_id, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this group is not allowed"
            )
        
        # Answer the question
        result = await ai_service.answer_question(
            question=request_data.question,
            group_id=request_data.group_id,
            user_id=user.get("sub"),
            is_premium=is_premium,
            use_cache=request_data.use_cache,
            context_type=request_data.context_type
        )
        
        # Log question for analytics in background
        background_tasks.add_task(
            log_question_analytics,
            user.get("sub"),
            request_data.question,
            request_data.group_id,
            result.get("source"),
            result.get("metrics", {})
        )
        
        return result
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )

@router.post("/search", response_model=SearchResponse)
async def search_content(
    request_data: SearchRequest,
    request: Request,
    ai_service: OptimizedAIService = Depends(get_ai_service),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Search for relevant content using semantic search
    """
    try:
        # Get user from request state
        user = request.state.user
        is_premium = request.state.is_premium
        
        # Validate group access
        if not await auth_service.verify_group_access(request_data.group_id, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this group is not allowed"
            )
        
        # Search for content
        start_time = __import__('time').time()
        results = await ai_service.search_relevant_content(
            question=request_data.query,
            group_id=request_data.group_id,
            community_id=request_data.community_id,
            is_premium=is_premium,
            top_k=request_data.limit
        )
        
        # Filter results by threshold
        filtered_results = [
            result for result in results 
            if result.get("similarity", 0.0) >= request_data.threshold
        ]
        
        # Prepare response
        response = {
            "results": filtered_results,
            "count": len(filtered_results),
            "query": request_data.query,
            "metrics": {
                "latency": __import__('time').time() - start_time,
                "total_results": len(results),
                "filtered_results": len(filtered_results)
            }
        }
        
        return response
    except Exception as e:
        logger.error(f"Error searching content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search content: {str(e)}"
        )

@router.get("/metrics", response_model=Dict[str, Any])
async def get_ai_metrics(
    request: Request,
    ai_service: OptimizedAIService = Depends(get_ai_service)
):
    """
    Get AI service performance metrics
    """
    try:
        # Only allow admin or service role
        user = request.state.user
        if user.get("role") not in ["admin", "service_role"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Get metrics
        metrics = await ai_service.get_performance_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting AI metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI metrics: {str(e)}"
        )

@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def submit_answer_feedback(
    feedback_data: Dict[str, Any],
    request: Request,
    supabase = Depends(get_supabase_client)
):
    """
    Submit feedback for an AI answer
    """
    try:
        # Get user from request state
        user = request.state.user
        
        # Prepare feedback data
        feedback_record = {
            "user_id": user.get("sub"),
            "question": feedback_data.get("question"),
            "answer": feedback_data.get("answer"),
            "rating": feedback_data.get("rating"),
            "feedback_text": feedback_data.get("feedback_text"),
            "group_id": feedback_data.get("group_id"),
            "created_at": __import__('datetime').datetime.now().isoformat()
        }
        
        # Store feedback in Supabase
        supabase.table("ai_feedback").insert(feedback_record).execute()
        
        return None
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

# Background task for analytics
async def log_question_analytics(
    user_id: str,
    question: str,
    group_id: str,
    source: str,
    metrics: Dict[str, Any]
):
    """Log question analytics for monitoring"""
    try:
        # This would typically send data to analytics service
        # For now, just log it
        logger.info(
            f"Question analytics: user={user_id}, group={group_id}, "
            f"source={source}, latency={metrics.get('latency', 0):.2f}s, "
            f"cache_hit={metrics.get('cache_hit', False)}"
        )
    except Exception as e:
        logger.error(f"Failed to log question analytics: {e}")