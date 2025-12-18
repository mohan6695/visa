"""
Community and social interaction models
Handles user communities, posts, comments, and engagement
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import SQLAlchemyBase


class CommunityType(PyEnum):
    """Types of communities"""
    PUBLIC = "public"
    PRIVATE = "private"
    COUNTRY_SPECIFIC = "country_specific"
    VISA_TYPE_SPECIFIC = "visa_type_specific"


class CommunityMembershipRole(PyEnum):
    """User roles in communities"""
    MEMBER = "member"
    MODERATOR = "moderator"
    ADMIN = "admin"
    OWNER = "owner"


class Community(SQLAlchemyBase):
    """Community model for user discussions"""
    
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    
    # Community type and visibility
    community_type = Column(String(20), default=CommunityType.PUBLIC.value, nullable=False)
    is_private = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    
    # Associated data
    country_id = Column(Integer, ForeignKey("country.id"), nullable=True)
    visa_type_id = Column(Integer, ForeignKey("visa_type.id"), nullable=True)
    
    # Moderation and rules
    rules = Column(JSON, default=list)
    moderation_guidelines = Column(Text)
    
    # Media and branding
    avatar_url = Column(String(500))
    banner_url = Column(String(500))
    
    # Statistics
    member_count = Column(Integer, default=0)
    post_count = Column(Integer, default=0)
    activity_score = Column(Integer, default=0)
    
    # Settings
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Relationships
    country = relationship("Country", back_populates="communities")
    memberships = relationship("CommunityMembership", back_populates="community", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="community", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_community_slug', 'slug'),
        Index('idx_community_type', 'community_type'),
        Index('idx_community_country', 'country_id'),
        Index('idx_community_active', 'is_active'),
        Index('idx_community_featured', 'is_featured'),
    )
    
    def __repr__(self) -> str:
        return f"<Community(id={self.id}, name='{self.name}', type='{self.community_type}')>"


class CommunityMembership(SQLAlchemyBase):
    """User membership in communities"""
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    community_id = Column(Integer, ForeignKey("community.id"), nullable=False)
    
    # Membership details
    role = Column(String(20), default=CommunityMembershipRole.MEMBER.value, nullable=False)
    is_approved = Column(Boolean, default=True)
    joined_at = Column(String(100))  # When user joined
    
    # Statistics
    posts_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    reputation_score = Column(Integer, default=0)
    
    # Status
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text)
    ban_expires_at = Column(String(100))
    
    # Relationships
    user = relationship("User")
    community = relationship("Community", back_populates="memberships")
    
    # Indexes
    __table_args__ = (
        Index('idx_community_membership_user', 'user_id'),
        Index('idx_community_membership_community', 'community_id'),
        Index('idx_community_membership_role', 'role'),
    )
    
    def __repr__(self) -> str:
        return f"<CommunityMembership(user_id={self.user_id}, community_id={self.community_id}, role='{self.role}')>"