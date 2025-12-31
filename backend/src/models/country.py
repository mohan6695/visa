from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Country(Base, TimestampMixin):
    """Model for country-specific information and settings"""
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True, nullable=False)  # usa, canada, uk, australia
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    flag_emoji = Column(String(10))  # Country flag emoji
    visa_types = Column(Text)  # JSON array of available visa types
    popular_cities = Column(Text)  # JSON array of popular cities
    requirements_url = Column(String(500))  # Link to official visa requirements
    processing_time = Column(String(100))  # Typical processing time
    fees_info = Column(Text)  # JSON with fee information
    is_active = Column(Boolean, default=True)
    
    # Relationships
    communities = relationship("Community", back_populates="country_obj")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_countries_code', 'code'),
        Index('idx_countries_name', 'name'),
        Index('idx_countries_is_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Country(id={self.id}, code='{self.code}', name='{self.name}')>"

class VisaType(Base, TimestampMixin):
    """Model for different visa types within countries"""
    __tablename__ = "visa_types"
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), nullable=False)  # Foreign key to countries.code
    type_code = Column(String(50), nullable=False)  # h1b, f1, tourist, etc.
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    eligibility_criteria = Column(Text)  # JSON with criteria
    required_documents = Column(Text)  # JSON with document list
    processing_time = Column(String(100))
    fees = Column(Text)  # JSON with fee breakdown
    restrictions = Column(Text)  # JSON with restrictions
    is_active = Column(Boolean, default=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_visa_types_country_code', 'country_code'),
        Index('idx_visa_types_type_code', 'type_code'),
        Index('idx_visa_types_is_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<VisaType(id={self.id}, country_code='{self.country_code}', type_code='{self.type_code}')>"

class VisaRequirement(Base, TimestampMixin):
    """Model for specific visa requirements and checklists"""
    __tablename__ = "visa_requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    visa_type_id = Column(Integer, nullable=False)  # Foreign key to visa_types.id
    requirement_type = Column(String(50), nullable=False)  # document, fee, test, etc.
    description = Column(Text, nullable=False)
    is_required = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # Display order
    notes = Column(Text)  # Additional notes or tips
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_visa_requirements_visa_type_id', 'visa_type_id'),
        Index('idx_visa_requirements_requirement_type', 'requirement_type'),
        Index('idx_visa_requirements_priority', 'priority'),
    )
    
    def __repr__(self):
        return f"<VisaRequirement(id={self.id}, visa_type_id={self.visa_type_id}, requirement_type='{self.requirement_type}')>"