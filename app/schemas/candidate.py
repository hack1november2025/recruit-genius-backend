from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class CandidateBase(BaseModel):
    """Base candidate schema."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = None
    resume_text: str | None = None
    resume_url: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: str | None = None
    education: str | None = None
    notes: str | None = None


class CandidateCreate(CandidateBase):
    """Schema for creating a candidate."""
    pass


class CandidateUpdate(BaseModel):
    """Schema for updating a candidate."""
    name: str | None = None
    phone: str | None = None
    resume_text: str | None = None
    resume_url: str | None = None
    skills: list[str] | None = None
    experience_years: str | None = None
    education: str | None = None
    status: str | None = None
    notes: str | None = None


class CandidateResponse(CandidateBase):
    """Schema for candidate response."""
    id: int
    status: str
    analysis: dict | None = None
    created_at: datetime
    updated_at: datetime | None = None
    
    class Config:
        from_attributes = True
