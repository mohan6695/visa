from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Notification(Base, TimestampMixin):
    """Notification model for user notifications"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # comment_reply, post_mention, community_invite, etc.
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    action_url = Column(String(500))  # URL to navigate to when clicked
    metadata = Column(Text)  # JSON string for additional data
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_notifications_user_id', 'user_id'),
        Index('idx_notifications_is_read', 'is_read'),
        Index('idx_notifications_type', 'type'),
        Index('idx_notifications_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}', is_read={self.is_read})>"

class PostLike(Base, TimestampMixin):
    """Association model for post likes"""
    __tablename__ = "post_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User")
    post = relationship("Post", back_populates="likes")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_post_likes_user_id', 'user_id'),
        Index('idx_post_likes_post_id', 'post_id'),
        Index('idx_post_likes_unique', 'user_id', 'post_id', unique=True),
    )
    
    def __repr__(self):
        return f"<PostLike(user_id={self.user_id}, post_id={self.post_id})>"

class CommentLike(Base, TimestampMixin):
    """Association model for comment likes"""
    __tablename__ = "comment_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User")
    comment = relationship("Comment", back_populates="likes")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_comment_likes_user_id', 'user_id'),
        Index('idx_comment_likes_comment_id', 'comment_id'),
        Index('idx_comment_likes_unique', 'user_id', 'comment_id', unique=True),
    )
    
    def __repr__(self):
        return f"<CommentLike(user_id={self.user_id}, comment_id={self.comment_id})>"