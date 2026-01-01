from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from typing import Optional, List, Dict, Any
import asyncio
import redis.asyncio as redis
from datetime import datetime, timedelta
import json
from pydantic import BaseModel, EmailStr, Field
import httpx
import hashlib
from supabase import create_client, Client
import stripe

# Import services and middleware
from .services.supabase_auth_service import SupabaseAuthService, get_auth_service
from .services.ai_service import AIService
from .services.embedding_service import EmbeddingService
from .services.chat_service import ChatService
from .services.search_service import SearchService
from .core.redis import redis_manager, get_redis
from .api.v1.middleware.auth_middleware import AuthMiddleware, PremiumMiddleware, RateLimitMiddleware

# Import API routers
from .api.v1.endpoints import auth, chat, ai, search, users, health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables with validation
class Settings:
    def __init__(self):
        # Supabase configuration
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
        
        # Redis configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Groq configuration
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.ai_provider = os.getenv("AI_PROVIDER", "groq")
        
        # Stripe configuration
        self.stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        self.stripe_publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
        
        # App configuration
        self.app_host = os.getenv("APP_HOST", "0.0.0.0")
        self.app_port = int(os.getenv("APP_PORT", "8000"))
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Security configuration
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
        
        # Validate required environment variables
        required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "REDIS_URL"]
        missing_vars = [var for var in required_vars if not getattr(self, var.lower())]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

settings = Settings()

# Initialize clients
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

# Stripe configuration
stripe.api_key = settings.stripe_secret_key

# Dependency to get Supabase client
def get_supabase_client() -> Client:
    return supabase

# Pydantic models
class UserProfile(BaseModel):
    user_id: str
    group_id: str
    is_premium: bool = False
    daily_posts: int = 0
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None

class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class PostCreate(BaseModel):
    group_id: str
    content: str = Field(..., min_length=1, max_length=5000)
    parent_id: Optional[str] = None

class CommentCreate(BaseModel):
    post_id: str
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[str] = None

class ChatMessage(BaseModel):
    group_id: str
    content: str = Field(..., min_length=1, max_length=1000)
    message_type: str = "text"  # text, image, file

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    group_id: Optional[str] = None
    limit: int = 10
    threshold: float = 0.7

class PremiumUpgradeRequest(BaseModel):
    price_id: str  # Stripe Price ID

class SubscriptionResponse(BaseModel):
    session_url: str

class UserPresence(BaseModel):
    group_id: str
    is_active: bool = True

# FastAPI app initialization
app = FastAPI(
    title="Visa Q&A Chat API",
    description="Real-time visa Q&A platform with group chat and premium features",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# Initialize services
async def startup_event():
    # Connect to Redis
    await redis_manager.connect()
    logger.info("Connected to Redis")

async def shutdown_event():
    # Disconnect from Redis
    await redis_manager.disconnect()
    logger.info("Disconnected from Redis")

app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

# Initialize auth service
auth_service = SupabaseAuthService(supabase)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware
app.add_middleware(
    AuthMiddleware,
    auth_service=auth_service,
    exclude_paths=[
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/reset-password",
    ]
)

app.add_middleware(
    PremiumMiddleware,
    premium_paths=[
        "/api/v1/premium/",
        "/api/v1/search/all",
    ]
)

app.add_middleware(
    RateLimitMiddleware,
    redis_client=redis_manager.get_client(),
    rate_limits={
        "default": 100,  # 100 requests per minute
        "search": 20,    # 20 search requests per minute
        "ai": 10,        # 10 AI requests per minute
    }
)

# Security middleware for production
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["visa-platform.com", "*.visa-platform.com", "api.visa-platform.com"]
    )

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(health.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test Redis connection
        await redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    try:
        # Test Supabase connection
        supabase_status = supabase.table("profiles").select("count").execute()
        supabase_db_status = "healthy"
    except Exception as e:
        supabase_db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "redis": redis_status,
            "supabase_db": supabase_db_status
        },
        "version": "1.0.0"
    }

# API Routes
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Visa Q&A Chat API",
        "version": "1.0.0",
        "docs": "/docs" if settings.environment != "production" else "disabled",
        "health": "/health"
    }

# User Profile Management
@app.get("/api/v1/user/profile/{user_id}")
async def get_user_profile(user_id: str):
    """Get user profile and premium status"""
    try:
        profile = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if not profile.data:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        return profile.data[0]
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Group Management
@app.post("/api/v1/groups")
async def create_group(group: GroupCreate):
    """Create a new group"""
    try:
        group_data = {
            "name": group.name,
            "description": group.description,
            "user_count": 0,
            "active_count": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("groups").insert(group_data).execute()
        return result.data[0]
    except Exception as e:
        logger.error(f"Error creating group: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create group")

@app.get("/api/v1/groups")
async def get_groups():
    """Get all groups with member counts"""
    try:
        groups = supabase.table("groups").select("*").order("created_at", desc=True).execute()
        return groups.data
    except Exception as e:
        logger.error(f"Error getting groups: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch groups")

@app.get("/api/v1/groups/{group_id}/stats")
async def get_group_stats(group_id: str):
    """Get group statistics including active users"""
    try:
        # Get active users count
        active_users = supabase.table("user_presence").select("count").eq("group_id", group_id).eq("is_active", True).gte("last_seen", (datetime.utcnow() - timedelta(minutes=5)).isoformat()).execute()
        
        # Get total posts count
        posts_count = supabase.table("posts").select("count").eq("group_id", group_id).execute()
        
        # Get recent activity
        recent_posts = supabase.table("posts").select("created_at").eq("group_id", group_id).gte("created_at", (datetime.utcnow() - timedelta(days=7)).isoformat()).execute()
        
        return {
            "group_id": group_id,
            "active_users": len(active_users.data),
            "total_posts": len(posts_count.data),
            "posts_this_week": len(recent_posts.data),
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting group stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch group statistics")

# Post Management
@app.post("/api/v1/posts")
async def create_post(post: PostCreate, background_tasks: BackgroundTasks):
    """Create a new post with auto-tagging"""
    try:
        # Generate watermark hash
        watermark_content = f"{post.content}{datetime.utcnow().isoformat()}"
        watermark_hash = hashlib.md5(watermark_content.encode()).hexdigest()
        
        # For now, set a default author_id (in real app, get from JWT token)
        author_id = "00000000-0000-0000-0000-000000000000"  # Default test user
        
        # Check user's daily post limit
        profile = supabase.table("profiles").select("*").eq("id", author_id).execute()
        if profile.data:
            user_profile = profile.data[0]
            if not user_profile["is_premium"] and user_profile["daily_posts"] >= 10:
                raise HTTPException(status_code=429, detail="Daily post limit reached. Upgrade to premium for unlimited posts.")
        
        post_data = {
            "group_id": post.group_id,
            "author_id": author_id,
            "content": post.content,
            "parent_id": post.parent_id,
            "watermark_hash": watermark_hash,
            "upvotes": 0,
            "downvotes": 0,
            "score": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("posts").insert(post_data).execute()
        new_post = result.data[0]
        
        # Increment user's daily posts count
        if not user_profile["is_premium"]:
            supabase.table("profiles").update({"daily_posts": user_profile["daily_posts"] + 1}).eq("id", author_id).execute()
        
        # Trigger auto-tagging in background
        background_tasks.add_task(auto_tag_post, new_post["id"], post.content)
        
        return new_post
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create post")

@app.get("/api/v1/groups/{group_id}/posts")
async def get_group_posts(group_id: str, limit: int = 20, offset: int = 0):
    """Get posts for a specific group with pagination"""
    try:
        posts = supabase.table("posts").select("*, profiles(username, avatar_url), post_tags(tags(name, category))").eq("group_id", group_id).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        return posts.data
    except Exception as e:
        logger.error(f"Error getting group posts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch posts")

# Comment Management
@app.post("/api/v1/comments")
async def create_comment(comment: CommentCreate):
    """Create a new comment"""
    try:
        # For now, set a default author_id (in real app, get from JWT token)
        author_id = "00000000-0000-0000-0000-000000000000"  # Default test user
        
        comment_data = {
            "post_id": comment.post_id,
            "author_id": author_id,
            "content": comment.content,
            "parent_id": comment.parent_id,
            "upvotes": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("comments").insert(comment_data).execute()
        return result.data[0]
    except Exception as e:
        logger.error(f"Error creating comment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create comment")

@app.get("/api/v1/posts/{post_id}/comments")
async def get_post_comments(post_id: str):
    """Get comments for a specific post"""
    try:
        comments = supabase.table("comments").select("*, profiles(username, avatar_url)").eq("post_id", post_id).order("created_at", desc=True).execute()
        return comments.data
    except Exception as e:
        logger.error(f"Error getting post comments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch comments")

# Background tasks
async def auto_tag_post(post_id: str, content: str):
    """Auto-tag a post using Groq LLM"""
    try:
        # Create embedding for the post content
        embedding = await create_embedding(content)
        
        # Update post with embedding
        supabase.table("posts").update({"embedding": embedding}).eq("id", post_id).execute()
        
        # Auto-tag using Groq
        await auto_tag_with_groq(post_id, content)
        
        # Find similar posts and inherit tags
        await inherit_similar_tags(post_id, embedding)
        
    except Exception as e:
        logger.error(f"Error in auto-tagging post {post_id}: {str(e)}")

async def create_embedding(text: str) -> List[float]:
    """Create embedding using Groq's embedding model"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.groq_api_url,
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mixtral-8x7b-32768",  # Use appropriate embedding model
                    "messages": [{"role": "user", "content": f"Create embedding for: {text}"}],
                    "max_tokens": 512
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                # For now, return a simple hash-based embedding (replace with actual embedding)
                embedding = [float(hash(text[i:i+10]) % 1000) / 1000.0 for i in range(0, len(text), 10)]
                return embedding[:384]  # Standard embedding size
            else:
                logger.error(f"Failed to create embedding: {response.status_code}")
                return [0.0] * 384
                
    except Exception as e:
        logger.error(f"Error creating embedding: {str(e)}")
        return [0.0] * 384

async def auto_tag_with_groq(post_id: str, content: str):
    """Auto-tag post using Groq LLM"""
    try:
        # Get available tags
        tags = supabase.table("tags").select("*").execute()
        tag_names = [tag["name"] for tag in tags.data]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.groq_api_url,
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {
                            "role": "system",
                            "content": f"Classify the following visa-related post into 1-3 relevant tags from this list: {', '.join(tag_names)}. Respond with JSON: {{\"tags\": [\"tag1\", \"tag2\"]}}"
                        },
                        {"role": "user", "content": content}
                    ],
                    "max_tokens": 100,
                    "temperature": 0.1
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content_response = result["choices"][0]["message"]["content"]
                
                try:
                    import json
                    tag_data = json.loads(content_response)
                    selected_tags = tag_data.get("tags", [])
                    
                    # Insert tag associations
                    for tag_name in selected_tags:
                        tag = next((t for t in tags.data if t["name"] == tag_name), None)
                        if tag:
                            supabase.table("post_tags").insert({
                                "post_id": post_id,
                                "tag_id": tag["id"]
                            }).execute()
                            
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse Groq response as JSON: {content_response}")
                    
    except Exception as e:
        logger.error(f"Error in auto-tagging with Groq: {str(e)}")

async def inherit_similar_tags(post_id: str, embedding: List[float]):
    """Inherit tags from similar posts"""
    try:
        # Find similar posts using vector similarity
        similar_posts = supabase.rpc('find_similar_posts', {
            'query_embedding': embedding,
            'match_threshold': 0.85,
            'match_count': 5
        }).execute()
        
        if similar_posts.data:
            # Get tags from the most similar post
            most_similar_post = similar_posts.data[0]
            existing_tags = supabase.table("post_tags").select("tag_id").eq("post_id", most_similar_post["id"]).execute()
            
            # Inherit up to 3 tags
            for tag_assoc in existing_tags.data[:3]:
                supabase.table("post_tags").insert({
                    "post_id": post_id,
                    "tag_id": tag_assoc["tag_id"]
                }).execute()
                
    except Exception as e:
        logger.error(f"Error inheriting similar tags: {str(e)}")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.environment == "development",
        log_level="info"
    )