"""
Notification and preference models
Handles user notifications and communication preferences
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from .base import SQLAlchemyBase


class NotificationType(PyEnum):
    """Types of notifications"""
    NEW_POST = "new_post"
    NEW_COMMENT = "new_comment"
    POST_LIKED = "post_liked"
    COMMENT_LIKED = "comment_liked"
    MENTION = "mention"
    COMMUNITY_INVITE = "community_invite"
    VISA_UPDATE = "visa_update"
    AI_SUGGESTION = "ai_suggestion"
    SYSTEM_ALERT = "system_alert"


class NotificationPriority(PyEnum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(SQLAlchemyBase):
    """User notification model"""
    
    # User association
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    # Notification details
    type = Column(String(30), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(10), default=NotificationPriority.NORMAL.value)
    
    # Related content
    related_user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    related_post_id = Column(Integer, ForeignKey("post.id"), nullable=True)
    related_comment_id = Column(Integer, ForeignKey("comment.id"), nullable=True)
    related_community_id = Column(Integer, ForeignKey("community.id"), nullable=True)
    
    # Notification metadata
    action_url = Column(String(500))
    image_url = Column(String(500))
    extra_data = Column(JSON)
    
    # Status
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    # Delivery tracking
    sent_at = Column(String(100))
    read_at = Column(String(100))
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    related_user = relationship("User", foreign_keys=[related_user_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_user', 'user_id'),
        Index('idx_notification_type', 'type'),
        Index('idx_notification_read', 'is_read'),
        Index('idx_notification_created', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}')>"


class NotificationPreference(SQLAlchemyBase):
    """User notification preferences"""
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    # Notification type preferences
    email_notifications = Column(JSON, default=dict)
    push_notifications = Column(JSON, default=dict)
    in_app_notifications = Column(JSON, default=dict)
    sms_notifications = Column(JSON, default=dict)
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(10))  # HH:MM format
    quiet_hours_end = Column(String(10))    # HH:MM format
    quiet_hours_timezone = Column(String(50), default="UTC")
    
    # Frequency settings
    digest_frequency = Column(String(20), default="daily")  # immediate, daily, weekly, never
    weekly_digest_day = Column(String(10), default="monday")
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_notification_preference_user', 'user_id'),
    )
    
    def __repr__(self) -> str:
        return f"<NotificationPreference(user_id={self.user_id})>"