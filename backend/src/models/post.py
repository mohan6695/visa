from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID, ARRAY
from sqlalchemy.types import Float
from sqlalchemy import case
from .base import Base, TimestampMixin
from ..utils.watermark import generate_watermark_hash, generate_display_watermark

class Post(Base, TimestampMixin):
    """Post model for visa Q&A discussions"""
    __tablename__ = "posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)  # Optional, can be set based on content
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=True)  # Optional for chat messages
    content = Column(Text, nullable=False)
    content_html = Column(Text)  # HTML version of content
    embedding = Column(ARRAY(Float), nullable=True)  # Vector embedding for semantic search
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    score = Column(Integer, default=0)  # Generated: upvotes - downvotes
    watermark_hash = Column(String(64), nullable=True)  # MD5 hash for DMCA tracking
    display_watermark = Column(String(50), nullable=True)  # User-friendly watermark like POST-xxxxx-epoch
    status = Column(String(20), default="published")  # published, draft, archived, deleted
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    search_vector = Column(TSVECTOR)  # Full-text search vector
    
    # Relationships
    author = relationship("User", back_populates="posts")
    group = relationship("Group", back_populates="posts")
    country = relationship("Country", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    post_tags = relationship("PostTag", back_populates="post", cascade="all, delete-orphan")
    
    # Composite index for performance
    __table_args__ = (
        Index('idx_posts_group_id', 'group_id'),
        Index('idx_posts_author_id', 'author_id'),
        Index('idx_posts_country_id', 'country_id'),
        Index('idx_posts_status', 'status'),
        Index('idx_posts_created_at', 'created_at'),
        Index('idx_posts_score', 'score'),
    )
    
    @property
    def net_score(self):
        """Calculate net score (upvotes - downvotes)"""
        return self.upvotes - self.downvotes
    
    def calculate_watermark_hash(self):
        """Generate watermark hash for DMCA tracking"""
        import hashlib
        content_to_hash = f"{self.content}{self.author_id}{self.created_at.isoformat()}"
        self.watermark_hash = hashlib.md5(content_to_hash.encode()).hexdigest()
    
    def update_score(self):
        """Update score based on upvotes and downvotes"""
        self.score = self.net_score
    
    def generate_display_watermark(self):
        """Generate user-friendly display watermark like POST-xxxxx-epoch"""
        import time
        from datetime import datetime
        epoch = int(time.time())
        # Extract first 4 chars of UUID for uniqueness
        uuid_part = str(self.id)[:8] if self.id else "0000"
        self.display_watermark = f"POST-{uuid_part}-{epoch}"
    
    def generate_all_watermarks(self):
        """Generate both watermark hash and display watermark"""
        self.calculate_watermark_hash()
        self.generate_display_watermark()
    
    def __repr__(self):
        return f"<Post(id={self.id}, group_id={self.group_id}, author_id={self.author_id}, score={self.score})>"