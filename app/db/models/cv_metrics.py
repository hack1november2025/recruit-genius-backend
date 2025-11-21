"""CV Metrics model for structured evaluation scores."""
from sqlalchemy import Column, Integer, Float, ForeignKey, JSON, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.db.base import Base


class CVMetrics(Base):
    """Structured metrics for CV evaluation against job requirements."""
    
    __tablename__ = "cv_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Core Fit Metrics
    skills_match_score = Column(Float, nullable=False, default=0.0)  # 0-100%
    experience_relevance_score = Column(Float, nullable=False, default=0.0)  # 0-10
    education_fit_score = Column(Float, nullable=False, default=0.0)  # 0-10
    
    # Quality Metrics
    achievement_impact_score = Column(Float, nullable=False, default=0.0)  # 0-10
    keyword_density_score = Column(Float, nullable=False, default=0.0)  # 0-100%
    
    # Risk/Confidence Metrics
    employment_gap_score = Column(Float, nullable=False, default=0.0)  # 0-10
    readability_score = Column(Float, nullable=False, default=0.0)  # 0-10
    ai_confidence_score = Column(Float, nullable=False, default=0.0)  # 0-100%
    
    # Composite Score
    composite_score = Column(Float, nullable=False, default=0.0)  # 0-100
    
    # Detailed breakdown
    metric_details = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('candidate_id', 'job_id', name='unique_candidate_job_metrics'),
    )
