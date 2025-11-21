from pydantic import BaseModel, Field
from datetime import datetime


class JobBase(BaseModel):
    """Base job schema."""
    title: str = Field(..., min_length=1, max_length=255)
    department: str | None = None
    location: str | None = None
    description: str = Field(..., min_length=1)
    requirements: str = Field(..., min_length=1)
    required_skills: list[str] = Field(default_factory=list)
    experience_required: str | None = None
    salary_range: str | None = None
    additional_info: dict | None = None


class JobCreate(JobBase):
    """Schema for creating a job."""
    pass


class JobUpdate(BaseModel):
    """Schema for updating a job."""
    title: str | None = None
    department: str | None = None
    location: str | None = None
    description: str | None = None
    requirements: str | None = None
    required_skills: list[str] | None = None
    experience_required: str | None = None
    salary_range: str | None = None
    status: str | None = None
    additional_info: dict | None = None


class JobResponse(JobBase):
    """Schema for job response."""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    
    class Config:
        from_attributes = True
