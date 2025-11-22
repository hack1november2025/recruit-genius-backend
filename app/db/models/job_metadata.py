"""Job Metadata model for structured job requirements."""
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Float, UniqueConstraint
from sqlalchemy.sql import func
from app.db.base import Base


class JobMetadata(Base):
    """Structured metadata extracted from job descriptions."""
    
    __tablename__ = "job_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Core Requirements
    required_skills = Column(JSON, default=list)  # List of required technical skills
    preferred_skills = Column(JSON, default=list)  # Nice-to-have skills
    min_experience_years = Column(Integer, nullable=True)
    max_experience_years = Column(Integer, nullable=True)
    
    # Education
    required_education = Column(String(100), nullable=True)  # e.g., "Bachelor's", "Master's"
    preferred_education = Column(String(100), nullable=True)
    
    # Location & Remote
    remote_type = Column(String(50), nullable=True)  # "remote", "hybrid", "onsite"
    locations = Column(JSON, default=list)  # List of acceptable locations
    
    # Seniority & Role
    seniority_level = Column(String(50), nullable=True)  # "junior", "mid", "senior", "lead"
    role_type = Column(String(50), nullable=True)  # "individual_contributor", "manager"
    
    # Compensation
    min_salary = Column(Float, nullable=True)
    max_salary = Column(Float, nullable=True)
    currency = Column(String(10), default="USD")
    
    # Certifications
    required_certifications = Column(JSON, default=list)
    preferred_certifications = Column(JSON, default=list)
    
    # Additional structured data
    responsibilities = Column(JSON, default=list)  # Key responsibilities
    benefits = Column(JSON, default=list)
    tech_stack = Column(JSON, default=list)  # Technologies used
    
    # Full metadata from LLM extraction
    full_metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('job_id', name='unique_job_metadata'),
    )
