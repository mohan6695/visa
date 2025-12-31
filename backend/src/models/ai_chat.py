from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Index, JSON
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class ChatSession(Base, TimestampMixin):
    """Model for AI chat sessions"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for anonymous
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(200))  # Auto-generated title from first message
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON)  # Additional session metadata
    
    # Relationships
    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_chat_sessions_user_id', 'user_id'),
        Index('idx_chat_sessions_session_id', 'session_id'),
        Index('idx_chat_sessions_is_active', 'is_active'),
        Index('idx_chat_sessions_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_id='{self.session_id}', user_id={self.user_id})>"

class ChatMessage(Base, TimestampMixin):
    """Model for individual chat messages"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default="text")  # text, image, file
    message_metadata = Column(JSON)  # Additional message metadata
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_chat_messages_session_id', 'session_id'),
        Index('idx_chat_messages_role', 'role'),
        Index('idx_chat_messages_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role='{self.role}')>"

class ChatContext(Base, TimestampMixin):
    """Model for chat context and knowledge base"""
    __tablename__ = "chat_context"
    
    id = Column(Integer, primary_key=True, index=True)
    context_key = Column(String(100), unique=True, index=True, nullable=False)
    context_data = Column(JSON, nullable=False)  # Context information
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    is_persistent = Column(Boolean, default=False)  # Whether to persist across sessions
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_chat_context_context_key', 'context_key'),
        Index('idx_chat_context_expires_at', 'expires_at'),
        Index('idx_chat_context_is_persistent', 'is_persistent'),
    )
    
    def __repr__(self):
        return f"<ChatContext(id={self.id}, context_key='{self.context_key}')>"

class ChatFeedback(Base, TimestampMixin):
    """Model for chat feedback and ratings"""
    __tablename__ = "chat_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)
    rating = Column(Integer)  # 1-5 star rating
    feedback_text = Column(Text)
    is_helpful = Column(Boolean)  # True/False if response was helpful
    
    # Relationships
    session = relationship("ChatSession")
    message = relationship("ChatMessage")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_chat_feedback_session_id', 'session_id'),
        Index('idx_chat_feedback_message_id', 'message_id'),
        Index('idx_chat_feedback_rating', 'rating'),
        Index('idx_chat_feedback_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ChatFeedback(id={self.id}, session_id={self.session_id}, rating={self.rating})>"