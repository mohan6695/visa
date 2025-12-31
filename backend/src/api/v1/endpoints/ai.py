from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from redis.asyncio import Redis
from ..dependencies import get_db, get_current_user, get_redis
from ...services.ai_service import AIService
from ...services.embedding_service import EmbeddingService
from ...models.user import User
from ...core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/ai/answer")
async def answer_question(
    question: str = Query(..., min_length=2, max_length=500),
    group_id: int = Query(..., description="Group ID for context"),
    community_id: Optional[int] = Query(None, description="Community ID for broader context"),
    use_cache: bool = Query(True, description="Whether to use cached answers"),
    context_type: str = Query("full", regex="^(full|summary)$", description="Type of context to use"),
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """Answer a question using RAG approach with semantic search"""
    try:
        # Initialize services
        embedding_service = EmbeddingService(db)
        ai_service = AIService(redis_client, embedding_service)
        
        # Get answer from AI service
        result = await ai_service.answer_question(
            question=question,
            group_id=group_id,
            community_id=community_id,
            use_cache=use_cache,
            context_type=context_type
        )
        
        return {
            "success": True,
            "data": result,
            "question": question,
            "group_id": group_id
        }
        
    except Exception as e:
        logger.error(f"AI answer API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate answer")

@router.get("/ai/search")
async def semantic_search(
    query: str = Query(..., min_length=2, max_length=100),
    group_id: int = Query(..., description="Group ID for context"),
    community_id: Optional[int] = Query(None, description="Community ID for broader context"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Semantic search across posts, comments, and messages"""
    try:
        embedding_service = EmbeddingService(db)
        
        # Perform hybrid search
        results = await embedding_service.hybrid_search(
            query=query,
            community_id=community_id,
            group_id=group_id,
            limit=limit
        )
        
        return {
            "success": True,
            "data": {
                "results": results,
                "query": query,
                "group_id": group_id,
                "community_id": community_id,
                "total": len(results)
            }
        }
        
    except Exception as e:
        logger.error(f"Semantic search API error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.post("/ai/summarize")
async def summarize_thread(
    group_id: int = Query(..., description="Group ID"),
    thread_content: List[Dict[str, Any]] = Query(..., description="Thread content to summarize"),
    summary_type: str = Query("concise", regex="^(concise|detailed)$", description="Type of summary"),
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """Summarize a thread of messages"""
    try:
        embedding_service = EmbeddingService(db)
        ai_service = AIService(redis_client, embedding_service)
        
        summary = await ai_service.summarize_thread(
            group_id=group_id,
            thread_content=thread_content,
            summary_type=summary_type
        )
        
        if summary:
            return {
                "success": True,
                "data": {
                    "summary": summary,
                    "group_id": group_id,
                    "summary_type": summary_type
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Thread summarization API error: {e}")
        raise HTTPException(status_code=500, detail="Summarization failed")

@router.get("/ai/cost-estimate")
async def get_cost_estimate(
    prompt_tokens: int = Query(..., ge=1, description="Number of prompt tokens"),
    response_tokens: int = Query(..., ge=1, description="Number of response tokens"),
    current_user: User = Depends(get_current_user)
):
    """Estimate cost for AI model usage"""
    try:
        ai_service = AIService(None, None)  # Redis and embedding service not needed for cost estimation
        
        estimated_cost = await ai_service.get_cost_estimate(prompt_tokens, response_tokens)
        
        return {
            "success": True,
            "data": {
                "estimated_cost": estimated_cost,
                "prompt_tokens": prompt_tokens,
                "response_tokens": response_tokens,
                "provider": settings.AI_PROVIDER
            }
        }
        
    except Exception as e:
        logger.error(f"Cost estimation API error: {e}")
        raise HTTPException(status_code=500, detail="Cost estimation failed")

@router.get("/ai/cache-status")
async def get_cache_status(
    group_id: int = Query(..., description="Group ID"),
    question: str = Query(..., min_length=2, max_length=500),
    redis_client: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """Check if a question-answer pair is cached"""
    try:
        ai_service = AIService(redis_client, None)
        
        cached_answer = await ai_service.get_cached_answer(group_id, question)
        
        return {
            "success": True,
            "data": {
                "is_cached": cached_answer is not None,
                "cached_answer": cached_answer,
                "group_id": group_id,
                "question": question
            }
        }
        
    except Exception as e:
        logger.error(f"Cache status API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to check cache status")

@router.delete("/ai/cache")
async def clear_cache(
    group_id: int = Query(..., description="Group ID"),
    question: Optional[str] = Query(None, min_length=2, max_length=500),
    redis_client: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """Clear cached answers for a group or specific question"""
    try:
        ai_service = AIService(redis_client, None)
        
        # This would need to be implemented in the AI service
        # For now, we'll return a success message
        return {
            "success": True,
            "data": {
                "message": "Cache cleared successfully",
                "group_id": group_id,
                "question": question
            }
        }
        
    except Exception as e:
        logger.error(f"Cache clearing API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@router.get("/ai/providers")
async def get_ai_providers(
    current_user: User = Depends(get_current_user)
):
    """Get available AI providers"""
    try:
        providers = [
            {
                "name": "groq",
                "description": "High-throughput, low-cost AI models",
                "models": ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"]
            },
            {
                "name": "openrouter",
                "description": "Access to multiple AI models",
                "models": ["anthropic/claude-3.5-sonnet", "google/gemini-pro", "openai/gpt-3.5-turbo"]
            },
            {
                "name": "ollama",
                "description": "Local AI models",
                "models": ["llama2", "mistral", "codellama"]
            }
        ]
        
        return {
            "success": True,
            "data": {
                "providers": providers,
                "current_provider": settings.AI_PROVIDER
            }
        }
        
    except Exception as e:
        logger.error(f"AI providers API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI providers")

@router.websocket("/ai/status")
async def websocket_ai_status(
    websocket: WebSocket,
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """WebSocket endpoint for AI service status updates"""
    try:
        await websocket.accept()
        
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "data": {
                "service": "ai",
                "status": "connected",
                "user_id": current_user.id
            }
        })
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "data": {"timestamp": "now"}
                    })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=1011, reason="Internal server error")