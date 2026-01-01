"""Database models for Visa Q&A Chat application"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


# Enums
class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class PostStatus(str, Enum):
    ACTIVE = "active"
    HIDDEN = "hidden"
    DELETED = "deleted"
    PENDING_REVIEW = "pending_review"


class TagCategory(str, Enum):
    VISA_TYPE = "visa_type"
    DOCUMENT = "document"
    PROCESS = "process"
    INTERVIEW = "interview"
    LOTTERY = "lottery"
    COUNTRY = "country"
    TIMELINE = "timeline"
    COST = "cost"


# Core Models
class UserProfile(BaseModel):
    """Extended user profile beyond Supabase Auth"""
    id: UUID = Field(default_factory=uuid4)
    auth_user_id: UUID
    group_id: Optional[UUID] = None
    display_name: str
    avatar_url: Optional[str] = None
    role: UserRole = UserRole.USER
    is_premium: bool = False
    daily_posts_used: int = 0
    daily_posts_limit: int = 10
    total_posts: int = 0
    total_upvotes: int = 0
    reputation_score: int = 0
    stripe_customer_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class Group(BaseModel):
    """Visa-related groups (H1B, F1, etc.)"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    slug: str = Field(unique=True)
    description: Optional[str] = None
    country: Optional[str] = None
    visa_type: Optional[str] = None
    user_count: int = 0
    active_count: int = 0
    is_public: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class Post(BaseModel):
    """StackOverflow-style Q&A posts"""
    id: UUID = Field(default_factory=uuid4)
    group_id: UUID
    author_id: UUID
    title: str
    content: str
    content_embedding: Optional[List[float]] = None
    status: PostStatus = PostStatus.ACTIVE
    upvotes: int = 0
    downvotes: int = 0
    score: int = 0
    view_count: int = 0
    answer_count: int = 0
    is_answered: bool = False
    accepted_answer_id: Optional[UUID] = None
    watermark_hash: str
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Comment(BaseModel):
    """Nested comments for posts"""
    id: UUID = Field(default_factory=uuid4)
    post_id: UUID
    parent_id: Optional[UUID] = None
    author_id: UUID
    content: str
    upvotes: int = 0
    score: int = 0
    is_accepted: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Tag(BaseModel):
    """Tags for categorizing posts"""
    id: int = Field(gt=0)
    name: str
    display_name: str
    category: TagCategory
    description: Optional[str] = None
    color: Optional[str] = None
    usage_count: int = 0
    is_moderator_only: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class PostTag(BaseModel):
    """Many-to-many relationship between posts and tags"""
    post_id: UUID
    tag_id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class UserPresence(BaseModel):
    """Real-time user presence tracking"""
    user_id: UUID
    group_id: UUID
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    device_info: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class GroupMessage(BaseModel):
    """Real-time chat messages within groups"""
    id: UUID = Field(default_factory=uuid4)
    group_id: UUID
    author_id: UUID
    content: str
    message_type: str = "text"  # text, image, file, etc.
    reply_to_id: Optional[UUID] = None
    edited_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


# Search and Analytics Models
class SearchResult(BaseModel):
    """Search result with hybrid ranking"""
    post_id: UUID
    title: str
    content: str
    author_name: str
    group_name: str
    tags: List[str]
    score: float
    similarity_score: float
    text_score: float
    upvotes: int
    created_at: datetime


class AutoTaggingResult(BaseModel):
    """Result from auto-tagging service"""
    post_id: UUID
    suggested_tags: List[str]
    confidence_scores: Dict[str, float]
    processing_time_ms: int
    model_used: str


class AnalyticsEvent(BaseModel):
    """Analytics event tracking"""
    id: UUID = Field(default_factory=uuid4)
    event_name: str
    user_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    properties: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# API Request/Response Models
class ChatMessageRequest(BaseModel):
    """Request model for chat messages"""
    group_id: UUID
    content: str = Field(min_length=1, max_length=2000)
    message_type: str = "text"
    reply_to_id: Optional[UUID] = None


class ChatMessageResponse(BaseModel):
    """Response model for chat messages"""
    id: UUID
    group_id: UUID
    author_name: str
    author_avatar: Optional[str]
    content: str
    message_type: str
    created_at: datetime
    is_edited: bool


class PostCreateRequest(BaseModel):
    """Request model for creating posts"""
    group_id: UUID
    title: str = Field(min_length=10, max_length=200)
    content: str = Field(min_length=20, max_length=10000)
    tags: List[str] = []


class PostResponse(BaseModel):
    """Response model for posts"""
    id: UUID
    title: str
    content: str
    author_name: str
    author_avatar: Optional[str]
    group_name: str
    tags: List[str]
    upvotes: int
    downvotes: int
    score: int
    view_count: int
    answer_count: int
    is_answered: bool
    created_at: datetime
    updated_at: Optional[datetime]


class SearchRequest(BaseModel):
    """Request model for search"""
    query: str = Field(min_length=1, max_length=500)
    group_id: Optional[UUID] = None
    tags: List[str] = []
    limit: int = Field(default=20, le=100)
    offset: int = Field(default=0)


class AIChatRequest(BaseModel):
    """Request model for AI chat"""
    group_id: UUID
    question: str = Field(min_length=1, max_length=1000)
    context_posts: List[UUID] = []
    use_cache: bool = True


class AIChatResponse(BaseModel):
    """Response model for AI chat"""
    answer: str
    sources: List[Dict[str, Any]] = []
    confidence_score: float
    processing_time_ms: int
    cached: bool = False


class UserStats(BaseModel):
    """User statistics"""
    total_posts: int
    total_upvotes: int
    reputation_score: int
    daily_posts_remaining: int
    is_premium: bool
    member_since: datetime


class GroupStats(BaseModel):
    """Group statistics"""
    total_users: int
    active_users: int
    total_posts: int
    posts_today: int
    top_contributors: List[Dict[str, Any]]