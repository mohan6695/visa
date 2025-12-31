from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class SearchQuery(Base, TimestampMixin):
    """Model to track search queries for analytics and suggestions"""
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(200), nullable=False)
    country = Column(String(50))  # Optional country filter
    search_type = Column(String(50))  # posts, comments, communities, all
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Optional
    result_count = Column(Integer, default=0)
    search_time = Column(Integer)  # Time taken for search in milliseconds
    
    # Relationships
    user = relationship("User")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_search_queries_query', 'query'),
        Index('idx_search_queries_country', 'country'),
        Index('idx_search_queries_search_type', 'search_type'),
        Index('idx_search_queries_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<SearchQuery(id={self.id}, query='{self.query}', country='{self.country}')>"

class SearchSuggestion(Base, TimestampMixin):
    """Model for search suggestions and autocomplete"""
    __tablename__ = "search_suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    suggestion = Column(String(200), nullable=False)
    country = Column(String(50))  # Optional country filter
    suggestion_type = Column(String(50))  # popular_query, trending_topic, related_term
    weight = Column(Integer, default=1)  # Popularity weight
    last_used = Column(DateTime, default=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_search_suggestions_suggestion', 'suggestion'),
        Index('idx_search_suggestions_country', 'country'),
        Index('idx_search_suggestions_suggestion_type', 'suggestion_type'),
        Index('idx_search_suggestions_weight', 'weight'),
        Index('idx_search_suggestions_last_used', 'last_used'),
    )
    
    def __repr__(self):
        return f"<SearchSuggestion(id={self.id}, suggestion='{self.suggestion}', weight={self.weight})>"

class TrendingTopic(Base, TimestampMixin):
    """Model for trending topics and discussions"""
    __tablename__ = "trending_topics"
    
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(200), nullable=False)
    country = Column(String(50), nullable=False)
    score = Column(Integer, default=0)  # Calculated trending score
    post_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    last_activity = Column(DateTime, default=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_trending_topics_topic', 'topic'),
        Index('idx_trending_topics_country', 'country'),
        Index('idx_trending_topics_score', 'score'),
        Index('idx_trending_topics_last_activity', 'last_activity'),
    )
    
    def __repr__(self):
        return f"<TrendingTopic(id={self.id}, topic='{self.topic}', country='{self.country}', score={self.score})>"