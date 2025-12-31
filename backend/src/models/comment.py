from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TSVECTOR
from .base import Base, TimestampMixin

class Comment(Base, TimestampMixin):
    """Comment model for post discussions and chat messages"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    content_html = Column(Text)  # HTML version of content
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)  # Null for chat messages
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # For nested comments
    status = Column(String(20), default="published")  # published, edited, deleted
    is_chat_message = Column(Boolean, default=False)  # True for chat messages
    message_type = Column(String(20), default="text")  # text, image, file
    like_count = Column(Integer, default=0)
    search_vector = Column(TSVECTOR)  # Full-text search vector
    
    # Relationships
    author = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    community = relationship("Community", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_comments_post_id', 'post_id'),
        Index('idx_comments_author_id', 'author_id'),
        Index('idx_comments_community_id', 'community_id'),
        Index('idx_comments_parent_id', 'parent_id'),
        Index('idx_comments_is_chat_message', 'is_chat_message'),
        Index('idx_comments_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Comment(id={self.id}, author_id={self.author_id}, post_id={self.post_id})>"