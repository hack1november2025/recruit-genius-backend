from sqlalchemy import Column, Integer, ForeignKey, Float, Text, JSON
from app.db.base import Base, TimestampMixin


class Match(Base, TimestampMixin):
    """Candidate-Job match model."""
    
    __tablename__ = "matches"
    
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    match_score = Column(Float, nullable=False)  # 0-100
    reasoning = Column(Text, nullable=True)
    matching_skills = Column(JSON, default=list, nullable=False)
    missing_skills = Column(JSON, default=list, nullable=False)
    ai_insights = Column(JSON, nullable=True)
