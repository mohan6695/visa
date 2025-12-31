from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TSVECTOR
from .base import Base, TimestampMixin

class Post(Base, TimestampMixin):
    """Post model for community discussions"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    content_html = Column(Text)  # HTML version of content
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    status = Column(String(20), default="published")  # published, draft, archived, deleted
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    tags = Column(String(500))  # Comma-separated tags
    search_vector = Column(TSVECTOR)  # Full-text search vector
    
    # Relationships
    author = relationship("User", back_populates="posts")
    community = relationship("Community", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_posts_community_id', 'community_id'),
        Index('idx_posts_author_id', 'author_id'),
        Index('idx_posts_status', 'status'),
        Index('idx_posts_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Post(id={self.id}, title='{self.title}', author_id={self.author_id})>"