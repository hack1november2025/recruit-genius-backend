from sqlalchemy import Column, String, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin
import enum


class JobStatus(str, enum.Enum):
    """Job posting status enum."""
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"


class Job(Base, TimestampMixin):
    """Job posting model."""
    
    __tablename__ = "jobs"
    
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)  # Full AI-generated description
    department = Column(String(100), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    salary_range = Column(String(100), nullable=True)
    status = Column(
        SQLEnum(JobStatus),
        default=JobStatus.DRAFT,
        nullable=False,
        index=True
    )
    additional_metadata = Column(JSON, nullable=True)  # Store generation metadata, skills, etc.
    
    # Relationships
    job_metadata = relationship("JobMetadata", uselist=False, back_populates="job", lazy="select")
