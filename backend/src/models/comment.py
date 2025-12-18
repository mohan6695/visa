"""
Comment models for post discussions
Handles threaded comments and engagement
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from .base import SQLAlchemyBase


class Comment(SQLAlchemyBase):
    """Comment model for post discussions"""
    
    # Content
    content = Column(Text, nullable=False)
    
    # Associations
    author_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("post.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comment.id"), nullable=True)  # For threading
    
    # Comment features
    mentions = Column(JSON, default=list)  # Mentioned users
    attachments = Column(JSON, default=list)  # File URLs and metadata
    
    # Engagement metrics
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    
    # Comment status
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    
    # Content moderation
    is_hidden = Column(Boolean, default=False)
    hidden_reason = Column(String(200))
    
    # Relationships
    author = relationship("User")
    post = relationship("Post", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_comment_author', 'author_id'),
        Index('idx_comment_post', 'post_id'),
        Index('idx_comment_parent', 'parent_id'),
        Index('idx_comment_created', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, post_id={self.post_id}, author_id={self.author_id})>"


class CommentLike(SQLAlchemyBase):
    """Comment likes from users"""
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    comment_id = Column(Integer, ForeignKey("comment.id"), nullable=False)
    
    # Like metadata
    like_type = Column(String(20), default="like")  # like, love, helpful, etc.
    
    # Relationships
    user = relationship("User")
    comment = relationship("Comment", back_populates="likes")
    
    # Indexes
    __table_args__ = (
        Index('idx_comment_like_user_comment', 'user_id', 'comment_id'),
        Index('idx_comment_like_comment', 'comment_id'),
    )
    
    def __repr__(self) -> str:
        return f"<CommentLike(user_id={self.user_id}, comment_id={self.comment_id}, type='{self.like_type}')>"