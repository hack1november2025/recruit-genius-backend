"""Schemas package."""
from app.schemas.candidate import CandidateCreate, CandidateUpdate, CandidateResponse
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.schemas.match import MatchCreate, MatchResponse, AnalyzeRequest

__all__ = [
    "CandidateCreate",
    "CandidateUpdate",
    "CandidateResponse",
    "JobCreate",
    "JobUpdate",
    "JobResponse",
    "MatchCreate",
    "MatchResponse",
    "AnalyzeRequest",
]
