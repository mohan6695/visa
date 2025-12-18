"""
Post and engagement models for community content
Handles posts, likes, bookmarks, and content management
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, JSON, Float, Index
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import SQLAlchemyBase


class PostType(PyEnum):
    """Types of posts"""
    DISCUSSION = "discussion"
    QUESTION = "question"
    EXPERIENCE = "experience"
    NEWS = "news"
    GUIDE = "guide"
    REVIEW = "review"


class PostStatus(PyEnum):
    """Post status"""
    PUBLISHED = "published"
    DRAFT = "draft"
    HIDDEN = "hidden"
    DELETED = "deleted"


class Post(SQLAlchemyBase):
    """Post model for community content"""
    
    # Content
    title = Column(String(300), nullable=False, index=True)
    content = Column(Text, nullable=False)
    post_type = Column(String(20), default=PostType.DISCUSSION.value, nullable=False)
    status = Column(String(20), default=PostStatus.PUBLISHED.value, nullable=False)
    
    # Associations
    author_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    community_id = Column(Integer, ForeignKey("community.id"), nullable=False)
    country_id = Column(Integer, ForeignKey("country.id"), nullable=True)
    visa_type_id = Column(Integer, ForeignKey("visa_type.id"), nullable=True)
    
    # Content features
    tags = Column(JSON, default=list)
    attachments = Column(JSON, default=list)  # File URLs and metadata
    mentions = Column(JSON, default=list)  # Mentioned users
    
    # Engagement metrics
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    bookmark_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    
    # Popularity and ranking
    engagement_score = Column(Float, default=0.0)
    trending_score = Column(Float, default=0.0)
    
    # Content moderation
    is_featured = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    is_solved = Column(Boolean, default=False)  # For questions
    
    # SEO and metadata
    slug = Column(String(300), index=True)
    meta_description = Column(String(500))
    canonical_url = Column(String(500))
    
    # Relationships
    author = relationship("User")
    community = relationship("Community", back_populates="posts")
    country = relationship("Country")
    visa_type = relationship("VisaType")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    bookmarks = relationship("PostBookmark", back_populates="post", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_post_author', 'author_id'),
        Index('idx_post_community', 'community_id'),
        Index('idx_post_type', 'post_type'),
        Index('idx_post_status', 'status'),
        Index('idx_post_created', 'created_at'),
        Index('idx_post_trending', 'trending_score'),
        Index('idx_post_featured', 'is_featured'),
        Index('idx_post_country', 'country_id'),
    )
    
    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title='{self.title[:50]}...', type='{self.post_type}')>"


class PostLike(SQLAlchemyBase):
    """Post likes from users"""
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("post.id"), nullable=False)
    
    # Like metadata
    like_type = Column(String(20), default="like")  # like, love, helpful, etc.
    
    # Relationships
    user = relationship("User")
    post = relationship("Post", back_populates="likes")
    
    # Indexes
    __table_args__ = (
        Index('idx_post_like_user_post', 'user_id', 'post_id'),
        Index('idx_post_like_post', 'post_id'),
    )
    
    def __repr__(self) -> str:
        return f"<PostLike(user_id={self.user_id}, post_id={self.post_id}, type='{self.like_type}')>"


class PostBookmark(SQLAlchemyBase):
    """User bookmarks for posts"""
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("post.id"), nullable=False)
    
    # Bookmark metadata
    folder_name = Column(String(100), default="default")
    notes = Column(Text)
    
    # Relationships
    user = relationship("User")
    post = relationship("Post", back_populates="bookmarks")
    
    # Indexes
    __table_args__ = (
        Index('idx_post_bookmark_user_post', 'user_id', 'post_id'),
        Index('idx_post_bookmark_user', 'user_id'),
    )
    
    def __repr__(self) -> str:
        return f"<PostBookmark(user_id={self.user_id}, post_id={self.post_id}, folder='{self.folder_name}')>"