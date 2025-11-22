"""Schemas for Job Metadata model."""
from pydantic import BaseModel
from datetime import datetime


class JobMetadataBase(BaseModel):
    """Base job metadata schema."""
    job_id: int
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    min_experience_years: int | None = None
    max_experience_years: int | None = None
    required_education: str | None = None
    preferred_education: str | None = None
    remote_type: str | None = None
    locations: list[str] = []
    seniority_level: str | None = None
    role_type: str | None = None
    min_salary: float | None = None
    max_salary: float | None = None
    currency: str = "USD"
    required_certifications: list[str] = []
    preferred_certifications: list[str] = []
    responsibilities: list[str] = []
    benefits: list[str] = []
    tech_stack: list[str] = []
    full_metadata: dict = {}


class JobMetadataCreate(JobMetadataBase):
    """Schema for creating job metadata."""
    pass


class JobMetadataResponse(JobMetadataBase):
    """Schema for job metadata response."""
    id: int
    created_at: datetime
    updated_at: datetime | None
    
    class Config:
        from_attributes = True
