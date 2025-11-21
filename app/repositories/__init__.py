"""Repositories package."""
from app.repositories.base import BaseRepository
from app.repositories.candidate import CandidateRepository
from app.repositories.job import JobRepository
from app.repositories.match import MatchRepository

__all__ = [
    "BaseRepository",
    "CandidateRepository",
    "JobRepository",
    "MatchRepository",
]
