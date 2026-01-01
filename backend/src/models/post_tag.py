from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class PostTag(Base, TimestampMixin):
    """Many-to-many relationship between posts and tags"""
    __tablename__ = "post_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)
    confidence = Column(String(5), default="auto")  # 'auto', 'manual', confidence score
    
    # Relationships
    post = relationship("Post", back_populates="post_tags")
    tag = relationship("Tag", back_populates="post_tags")
    
    # Composite primary key to prevent duplicates
    __table_args__ = (
        Index('idx_post_tags_post_id', 'post_id'),
        Index('idx_post_tags_tag_id', 'tag_id'),
    )
    
    def __repr__(self):
        return f"<PostTag(post_id={self.post_id}, tag_id={self.tag_id})>"