"""
User models for authentication and profile management
Optimized for high-scale user management with proper indexing
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext

from .base import SQLAlchemyBase

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(SQLAlchemyBase):
    """User model for authentication and basic info"""
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    
    # Account management
    last_login = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    
    # Profile relationship
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def verify_password(self, plain_password: str) -> bool:
        """Verify user password"""
        return pwd_context.verify(plain_password, self.hashed_password)
    
    def set_password(self, password: str) -> None:
        """Hash and set user password"""
        self.hashed_password = pwd_context.hash(password)
    
    def update_login(self) -> None:
        """Update login statistics"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class UserProfile(SQLAlchemyBase):
    """Extended user profile information"""
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("user.id"), unique=True, nullable=False)
    
    # Personal information
    first_name = Column(String(100))
    last_name = Column(String(100))
    bio = Column(Text)
    avatar_url = Column(String(500))
    
    # Location information
    country_id = Column(Integer, ForeignKey("country.id"), nullable=True)
    timezone = Column(String(50), default="UTC")
    preferred_language = Column(String(10), default="en")
    
    # Preferences
    notification_preferences = Column(JSON, default=dict)
    privacy_settings = Column(JSON, default=dict)
    
    # Statistics
    posts_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    reputation_score = Column(Integer, default=0)
    
    # Relationship
    user = relationship("User", back_populates="profile")
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or ""
    
    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id}, full_name='{self.full_name}')>"