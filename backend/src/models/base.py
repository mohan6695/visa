"""
Base database model with common fields and functionality
Optimized for scalability with proper indexing and constraints
"""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base, declared_attr
import uuid


class Base:
    """Base model class with common fields and methods"""
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name (snake_case)"""
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    # Primary key using UUID for distributed systems
    id = Column(Integer, primary_key=True, index=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    # Soft delete for data retention
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def update(self, **kwargs) -> None:
        """Update model fields"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted"""
        return self.deleted_at is not None
    
    def soft_delete(self) -> None:
        """Soft delete the record"""
        self.deleted_at = datetime.utcnow()


# Create declarative base
SQLAlchemyBase = declarative_base(cls=Base)