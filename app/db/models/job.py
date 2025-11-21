from sqlalchemy import Column, String, Text, JSON, Enum as SQLEnum
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
    department = Column(String(100), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list, nullable=False)  # List of skills
    experience_required = Column(String(50), nullable=True)
    salary_range = Column(String(100), nullable=True)
    status = Column(
        SQLEnum(JobStatus),
        default=JobStatus.DRAFT,
        nullable=False,
        index=True
    )
    additional_info = Column(JSON, nullable=True)
