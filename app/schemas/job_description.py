"""Schemas for job description generation."""
from pydantic import BaseModel, Field
from typing import Literal


class JobDescriptionGenerateRequest(BaseModel):
    """Request schema for job description generation."""
    brief_description: str = Field(..., min_length=10, max_length=1000, 
                                   description="Brief description of the role")
    department: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=255)
    employment_type: str | None = Field(None, 
                                       description="e.g., Full-time, Part-time, Contract")
    salary_range: str | None = Field(None, max_length=100)
    tone: Literal["formal", "friendly", "inclusive"] = Field(default="professional", 
                                                              description="Tone of the job posting")


class JobDescriptionResponse(BaseModel):
    """Response schema for generated job description."""
    job_title: str
    full_description: str
    responsibilities: list[str]
    required_qualifications: list[str]
    preferred_qualifications: list[str]
    benefits: list[str]
    inclusivity_score: float
    flagged_terms: list[str]
    generation_time_ms: int
    
    # Metadata for user to review
    department: str | None = None
    location: str | None = None
    employment_type: str | None = None
    salary_range: str | None = None


class JobCreateFromDescription(BaseModel):
    """Schema for creating a job from generated description."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=100, 
                            description="Full generated description")
    department: str | None = None
    location: str | None = None
    salary_range: str | None = None
