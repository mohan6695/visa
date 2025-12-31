from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TSVECTOR, VECTOR
from .base import Base, TimestampMixin

class GroupMessage(Base, TimestampMixin):
    """Group message model for chat functionality"""
    __tablename__ = "group_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    content_html = Column(Text)  # HTML version of content
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    message_type = Column(String(20), default="text")  # text, image, file
    status = Column(String(20), default="published")  # published, edited, deleted
    like_count = Column(Integer, default=0)
    search_vector = Column(TSVECTOR)  # Full-text search vector
    content_embedding = Column(VECTOR(1536))  # pgvector embedding for semantic search
    
    # Relationships
    user = relationship("User", back_populates="group_messages")
    group = relationship("Community", back_populates="group_messages")
    likes = relationship("GroupMessageLike", back_populates="message", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_group_messages_group_id', 'group_id'),
        Index('idx_group_messages_user_id', 'user_id'),
        Index('idx_group_messages_created_at', 'created_at'),
        Index('idx_group_messages_status', 'status'),
        Index('idx_group_messages_search_vector', 'search_vector', postgresql_using='gin'),
        Index('idx_group_messages_content_embedding', 'content_embedding', postgresql_using='ivfflat'),
    )
    
    def __repr__(self):
        return f"<GroupMessage(id={self.id}, user_id={self.user_id}, group_id={self.group_id})>"

class GroupMessageLike(Base, TimestampMixin):
    """Association model for group message likes"""
    __tablename__ = "group_message_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("group_messages.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User")
    message = relationship("GroupMessage", back_populates="likes")
    
    # Unique constraint to prevent duplicate likes
    __table_args__ = (
        Index('idx_group_message_likes_user_message', 'user_id', 'message_id', unique=True),
    )
    
    def __repr__(self):
        return f"<GroupMessageLike(user_id={self.user_id}, message_id={self.message_id})>"

class MessageReadReceipt(Base, TimestampMixin):
    """Read receipts for group messages"""
    __tablename__ = "message_read_receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("group_messages.id"), nullable=False)
    read_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User")
    group = relationship("Community")
    message = relationship("GroupMessage")
    
    # Unique constraint
    __table_args__ = (
        Index('idx_message_read_receipts_user_group_message', 'user_id', 'group_id', 'message_id', unique=True),
    )
    
    def __repr__(self):
        return f"<MessageReadReceipt(user_id={self.user_id}, group_id={self.group_id}, message_id={self.message_id})>"

class UserPresence(Base, TimestampMixin):
    """User presence tracking for groups"""
    __tablename__ = "user_presence"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("communities.id"), primary_key=True)
    last_seen = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User")
    group = relationship("Community")
    
    def __repr__(self):
        return f"<UserPresence(user_id={self.user_id}, group_id={self.group_id}, last_seen={self.last_seen})>"