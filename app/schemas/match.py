from pydantic import BaseModel, Field
from datetime import datetime


class MatchCreate(BaseModel):
    """Schema for creating a match."""
    candidate_id: int
    job_id: int


class MatchResponse(BaseModel):
    """Schema for match response."""
    id: int
    candidate_id: int
    job_id: int
    match_score: float = Field(..., ge=0, le=100)
    reasoning: str | None = None
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    ai_insights: dict | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalyzeRequest(BaseModel):
    """Schema for resume analysis request."""
    candidate_id: int
