"""
Search and analytics models
Handles search history and user behavior analytics
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Float, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from .base import SQLAlchemyBase


class SearchHistory(SQLAlchemyBase):
    """User search history model"""
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    # Search details
    query = Column(String(500), nullable=False)
    search_type = Column(String(50))  # country, visa, posts, users, general
    filters = Column(JSON)  # Applied filters
    
    # Search results
    results_count = Column(Integer, default=0)
    clicked_result_id = Column(Integer)  # ID of clicked result
    clicked_result_type = Column(String(50))  # post, country, visa, etc.
    
    # Search metadata
    search_duration = Column(Float)  # Time spent searching in seconds
    is_autocomplete = Column(Boolean, default=False)
    search_source = Column(String(50))  # header_search, advanced_search, etc.
    
    # Session context
    session_id = Column(String(100))
    user_agent = Column(Text)
    ip_address = Column(String(45))
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_search_history_user', 'user_id'),
        Index('idx_search_history_query', 'query'),
        Index('idx_search_history_type', 'search_type'),
        Index('idx_search_history_created', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<SearchHistory(id={self.id}, user_id={self.user_id}, query='{self.query[:50]}...')>"