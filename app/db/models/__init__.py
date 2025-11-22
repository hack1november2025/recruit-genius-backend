"""Database models."""
from app.db.models.candidate import Candidate, CandidateStatus
from app.db.models.job import Job, JobStatus
from app.db.models.match import Match
from app.db.models.cv import CV
from app.db.models.cv_metrics import CVMetrics
from app.db.models.job_metadata import JobMetadata

__all__ = [
    "Candidate",
    "CandidateStatus",
    "Job",
    "JobStatus",
    "Match",
    "CV",
    "CVMetrics",
    "JobMetadata",
]
