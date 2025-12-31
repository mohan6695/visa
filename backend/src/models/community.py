from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TSVECTOR
from .base import Base, TimestampMixin

class Community(Base, TimestampMixin):
    """Community model for organizing discussions by country/topic"""
    __tablename__ = "communities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    description_html = Column(Text)  # HTML version of description
    country = Column(String(50), nullable=False)  # usa, canada, uk, australia
    slug = Column(String(100), unique=True, index=True, nullable=False)
    is_public = Column(Boolean, default=True)
    is_moderated = Column(Boolean, default=True)
    member_count = Column(Integer, default=0)
    post_count = Column(Integer, default=0)
    avatar_url = Column(String(500))
    banner_url = Column(String(500))
    rules = Column(Text)  # Community rules
    search_vector = Column(TSVECTOR)  # Full-text search vector
    
    # Relationships
    posts = relationship("Post", back_populates="community", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="community", cascade="all, delete-orphan")
    members = relationship("CommunityMember", back_populates="community", cascade="all, delete-orphan")
    moderators = relationship("CommunityModerator", back_populates="community", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_communities_country', 'country'),
        Index('idx_communities_slug', 'slug'),
        Index('idx_communities_is_public', 'is_public'),
        Index('idx_communities_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Community(id={self.id}, name='{self.name}', country='{self.country}')>"

class CommunityMember(Base, TimestampMixin):
    """Association model for community membership"""
    __tablename__ = "community_members"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    role = Column(String(20), default="member")  # member, moderator, admin
    joined_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="communities")
    community = relationship("Community", back_populates="members")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_community_members_user_id', 'user_id'),
        Index('idx_community_members_community_id', 'community_id'),
        Index('idx_community_members_role', 'role'),
    )
    
    def __repr__(self):
        return f"<CommunityMember(user_id={self.user_id}, community_id={self.community_id}, role='{self.role}')>"

class CommunityModerator(Base, TimestampMixin):
    """Association model for community moderation"""
    __tablename__ = "community_moderators"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    permissions = Column(String(200))  # Comma-separated permissions
    appointed_by = Column(Integer, ForeignKey("users.id"))  # Who appointed this moderator
    appointed_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    community = relationship("Community", back_populates="moderators")
    appointed_by_user = relationship("User", foreign_keys=[appointed_by])
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_community_moderators_user_id', 'user_id'),
        Index('idx_community_moderators_community_id', 'community_id'),
    )
    
    def __repr__(self):
        return f"<CommunityModerator(user_id={self.user_id}, community_id={self.community_id})>"