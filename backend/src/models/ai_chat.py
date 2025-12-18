"""
AI chat models for intelligent visa assistance
Implements RAG (Retrieval Augmented Generation) system
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Float, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import SQLAlchemyBase


class ChatSessionStatus(PyEnum):
    """Chat session status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageRole(PyEnum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(SQLAlchemyBase):
    """AI chat session model"""
    
    # User association
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    # Session metadata
    title = Column(String(200))
    topic = Column(String(100))  # visa_question, country_info, embassy_info, etc.
    context_data = Column(JSON)  # country_id, visa_type_id, etc.
    
    # Session configuration
    model_used = Column(String(50))  # gpt-4, claude-3, llama-3, etc.
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    
    # Session statistics
    message_count = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Status and metadata
    status = Column(String(20), default=ChatSessionStatus.ACTIVE.value)
    is_feedback_provided = Column(Boolean, default=False)
    feedback_rating = Column(Integer)  # 1-5 stars
    feedback_text = Column(Text)
    
    # Relationships
    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_chat_session_user', 'user_id'),
        Index('idx_chat_session_status', 'status'),
        Index('idx_chat_session_created', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, topic='{self.topic}')>"


class ChatMessage(SQLAlchemyBase):
    """Individual chat messages"""
    
    # Session association
    session_id = Column(Integer, ForeignKey("chat_session.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # AI-specific metadata
    model_used = Column(String(50))
    tokens_used = Column(Integer, default=0)
    response_time = Column(Float)  # in seconds
    confidence_score = Column(Float)  # AI confidence 0-1
    
    # RAG context
    context_documents = Column(JSON, default=list)  # Retrieved documents
    embeddings_vector = Column(JSON)  # Vector representation
    search_queries = Column(JSON, default=list)  # What was searched
    
    # User feedback
    is_helpful = Column(Boolean)
    user_rating = Column(Integer)
    feedback_text = Column(Text)
    
    # Message features
    has_attachments = Column(Boolean, default=False)
    attachments = Column(JSON, default=list)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index('idx_chat_message_session', 'session_id'),
        Index('idx_chat_message_role', 'role'),
        Index('idx_chat_message_created', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role='{self.role}')>"