"""Database models for the application"""

from .base import Base
from .user import User, UserProfile, UserPresence
from .group_message import GroupMessage
from .post import Post, Comment, PostTag, Tag
from .notification import Notification
from .search import SearchResult, SearchRequest
from .ai_chat import AIChatRequest, AIChatResponse, ChatMessageRequest, ChatMessageResponse
from .community import Community
from .country import Country
from .visa_models import (
    UserProfile as VisaUserProfile,
    Group,
    Post as VisaPost,
    Comment as VisaComment,
    Tag as VisaTag,
    PostTag as VisaPostTag,
    UserPresence as VisaUserPresence,
    GroupMessage as VisaGroupMessage,
    SearchResult as VisaSearchResult,
    AutoTaggingResult,
    AnalyticsEvent,
    ChatMessageRequest as VisaChatMessageRequest,
    ChatMessageResponse as VisaChatMessageResponse,
    PostCreateRequest,
    PostResponse,
    SearchRequest as VisaSearchRequest,
    AIChatRequest as VisaAIChatRequest,
    AIChatResponse as VisaAIChatResponse,
    UserStats,
    GroupStats,
    UserRole,
    PostStatus,
    TagCategory
)

__all__ = [
    # Base
    "Base",
    
    # Original models
    "User",
    "UserProfile", 
    "UserPresence",
    "GroupMessage",
    "Post",
    "Comment", 
    "PostTag",
    "Tag",
    "Notification",
    "SearchResult",
    "SearchRequest",
    "AIChatRequest",
    "AIChatResponse",
    "ChatMessageRequest",
    "ChatMessageResponse",
    "Community",
    "Country",
    
    # Visa-specific models
    "VisaUserProfile",
    "Group",
    "VisaPost",
    "VisaComment",
    "VisaTag",
    "VisaPostTag", 
    "VisaUserPresence",
    "VisaGroupMessage",
    "VisaSearchResult",
    "AutoTaggingResult",
    "AnalyticsEvent",
    "VisaChatMessageRequest",
    "VisaChatMessageResponse",
    "PostCreateRequest",
    "PostResponse",
    "VisaSearchRequest",
    "VisaAIChatRequest", 
    "VisaAIChatResponse",
    "UserStats",
    "GroupStats",
    
    # Enums
    "UserRole",
    "PostStatus",
    "TagCategory"
]