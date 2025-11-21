from sqlalchemy import Column, String, Text, JSON, Enum as SQLEnum
from app.db.base import Base, TimestampMixin
import enum


class CandidateStatus(str, enum.Enum):
    """Candidate status enum."""
    NEW = "new"
    SCREENING = "screening"
    INTERVIEWED = "interviewed"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"


class Candidate(Base, TimestampMixin):
    """Candidate model."""
    
    __tablename__ = "candidates"
    
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    resume_text = Column(Text, nullable=True)
    resume_url = Column(String(500), nullable=True)
    skills = Column(JSON, default=list, nullable=False)  # List of skills
    experience_years = Column(String(50), nullable=True)
    education = Column(Text, nullable=True)
    status = Column(
        SQLEnum(CandidateStatus),
        default=CandidateStatus.NEW,
        nullable=False,
        index=True
    )
    analysis = Column(JSON, nullable=True)  # AI analysis results
    notes = Column(Text, nullable=True)
