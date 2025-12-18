"""
Country and visa-related models
Core data structure for visa information platform
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import SQLAlchemyBase


class Country(SQLAlchemyBase):
    """Country information model"""
    
    # Basic information
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(3), nullable=False, unique=True, index=True)  # ISO 3166-1 alpha-3
    capital = Column(String(100))
    region = Column(String(50))
    subregion = Column(String(50))
    
    # Geographic data
    latitude = Column(Float)
    longitude = Column(Float)
    timezone = Column(String(100))
    
    # Statistics
    population = Column(Integer)
    area = Column(Float)  # in square kilometers
    
    # Flags and media
    flag_url = Column(String(500))
    coat_of_arms_url = Column(String(500))
    
    # Additional data
    currency = Column(String(10))
    languages = Column(JSON)  # List of languages
    calling_codes = Column(JSON)  # List of calling codes
    
    # Visa-related information
    visa_required_for_tourist = Column(Boolean, default=True)
    visa_required_for_business = Column(Boolean, default=True)
    embassy_info = Column(Text)
    
    # Statistics
    posts_count = Column(Integer, default=0)
    active_communities = Column(Integer, default=0)
    
    # Relationships
    visa_types = relationship("VisaType", back_populates="country", cascade="all, delete-orphan")
    communities = relationship("Community", back_populates="country")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_country_name', 'name'),
        Index('idx_country_code', 'code'),
        Index('idx_country_region', 'region'),
    )
    
    def __repr__(self) -> str:
        return f"<Country(id={self.id}, name='{self.name}', code='{self.code}')>"


class VisaType(SQLAlchemyBase):
    """Types of visas for each country"""
    
    country_id = Column(Integer, ForeignKey("country.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False)  # e.g., "B1", "F1", "H1B"
    category = Column(String(50))  # tourist, business, work, student, etc.
    
    # Requirements and information
    description = Column(Text)
    requirements = Column(JSON)  # List of requirements
    documents_needed = Column(JSON)  # List of documents
    processing_time = Column(String(100))  # e.g., "5-7 business days"
    fee_amount = Column(Float)
    fee_currency = Column(String(10))
    
    # Validity information
    validity_period = Column(String(100))  # e.g., "6 months"
    max_stay = Column(String(100))  # e.g., "30 days"
    multiple_entry = Column(Boolean, default=False)
    
    # Additional information
    restrictions = Column(JSON)
    special_notes = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_updated = Column(String(100))  # When requirements were last updated
    
    # Relationships
    country = relationship("Country", back_populates="visa_types")
    requirements_detail = relationship("VisaRequirement", back_populates="visa_type", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_visa_type_country', 'country_id'),
        Index('idx_visa_type_category', 'category'),
        Index('idx_visa_type_active', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<VisaType(id={self.id}, name='{self.name}', code='{self.code}')>"


class VisaRequirement(SQLAlchemyBase):
    """Detailed visa requirements"""
    
    visa_type_id = Column(Integer, ForeignKey("visa_type.id"), nullable=False)
    requirement_type = Column(String(50))  # mandatory, optional, conditional
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Requirement details
    is_physical_document = Column(Boolean, default=False)
    can_be_digital = Column(Boolean, default=False)
    expires_after = Column(String(100))  # e.g., "6 months"
    
    # Additional metadata
    category = Column(String(50))  # financial, medical, travel, etc.
    priority = Column(Integer, default=1)  # 1=high, 2=medium, 3=low
    
    # Relationship
    visa_type = relationship("VisaType", back_populates="requirements_detail")
    
    # Indexes
    __table_args__ = (
        Index('idx_visa_requirement_type', 'visa_type_id'),
        Index('idx_visa_requirement_category', 'category'),
    )
    
    def __repr__(self) -> str:
        return f"<VisaRequirement(id={self.id}, title='{self.title}', type='{self.requirement_type}')>"