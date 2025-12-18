"""
Database models for Visa Platform
Implements scalable schema for handling 500K-2M users
"""

from .base import SQLAlchemyBase
from .user import User, UserProfile
from .country import Country, VisaType, VisaRequirement
from .community import Community, CommunityMembership
from .post import Post, PostLike, PostBookmark
from .comment import Comment, CommentLike
from .ai_chat import ChatSession, ChatMessage
from .notification import Notification, NotificationPreference
from .search import SearchHistory

__all__ = [
    "SQLAlchemyBase",
    "User",
    "UserProfile",
    "Country",
    "VisaType",
    "VisaRequirement",
    "Community",
    "CommunityMembership",
    "Post",
    "PostLike",
    "PostBookmark",
    "Comment",
    "CommentLike",
    "ChatSession",
    "ChatMessage",
    "Notification",
    "NotificationPreference",
    "SearchHistory"
]