from fastapi import APIRouter
from . import auth, chat, search, users, ai, health, supabase_posts

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(supabase_posts.router, prefix="/supabase", tags=["supabase"])