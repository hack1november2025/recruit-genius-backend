"""Schemas for matcher agent requests and responses."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any


class MatcherRequest(BaseModel):
    """Request schema for job-candidate matching."""
    
    job_id: int = Field(..., description="Job ID to match candidates against")
    top_k: int = Field(10, ge=1, le=50, description="Maximum number of candidates to return")
    hard_constraints_overrides: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional constraints to override job metadata"
    )
    persist_matches: bool = Field(
        True,
        description="Whether to save matches to database"
    )


class ExperienceInfo(BaseModel):
    """Experience information for a candidate."""
    
    total_years_experience: int = Field(..., description="Total years of professional experience")
    relevant_experience_years: int = Field(..., description="Years of relevant experience")
    relevant_summary: str = Field(..., description="Brief summary of relevant experience")


class LocationMatchInfo(BaseModel):
    """Location compatibility information."""
    
    job_location_type: str = Field(..., description="Job location type (On-site/Remote/Hybrid)")
    candidate_location_type_preference: str = Field(
        ...,
        description="Candidate's location preference"
    )
    compatible: bool = Field(..., description="Whether locations are compatible")
    notes: str = Field(..., description="Additional location compatibility notes")


class LanguageMatchInfo(BaseModel):
    """Language compatibility information."""
    
    job_languages_required: List[str] = Field(..., description="Languages required by the job")
    candidate_languages: List[str] = Field(..., description="Languages the candidate speaks")
    compatible: bool = Field(..., description="Whether language requirements are met")


class CandidateMatch(BaseModel):
    """Detailed match information for a single candidate."""
    
    candidate_id: int = Field(..., description="Candidate ID")
    name: str = Field(..., description="Candidate name")
    current_role: str = Field(..., description="Current or most recent role")
    match_score: float = Field(..., ge=0, le=100, description="Overall match score (0-100)")
    hybrid_similarity_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Semantic similarity score from vector search"
    )
    
    # Skills analysis
    matched_skills: List[str] = Field(..., description="Required skills the candidate has")
    missing_required_skills: List[str] = Field(..., description="Required skills the candidate lacks")
    nice_to_have_skills_covered: List[str] = Field(
        ...,
        description="Nice-to-have skills the candidate has"
    )
    
    # Match dimensions
    seniority_match: str = Field(
        ...,
        description="Seniority alignment (Exact/Overqualified/Underqualified)"
    )
    experience: ExperienceInfo = Field(..., description="Experience details")
    location_match: LocationMatchInfo = Field(..., description="Location compatibility")
    language_match: LanguageMatchInfo = Field(..., description="Language compatibility")
    
    # Additional context
    other_relevant_factors: List[str] = Field(
        default_factory=list,
        description="Other relevant factors (availability, achievements, etc.)"
    )
    overall_rationale: str = Field(
        ...,
        description="Clear explanation of why this candidate matches the job"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": 123,
                "name": "John Doe",
                "current_role": "Senior Backend Engineer",
                "match_score": 87.5,
                "hybrid_similarity_score": 0.89,
                "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
                "missing_required_skills": ["Kubernetes"],
                "nice_to_have_skills_covered": ["Docker"],
                "seniority_match": "Exact",
                "experience": {
                    "total_years_experience": 8,
                    "relevant_experience_years": 6,
                    "relevant_summary": "6 years building scalable backend systems..."
                },
                "location_match": {
                    "job_location_type": "Remote",
                    "candidate_location_type_preference": "Remote",
                    "compatible": True,
                    "notes": "Fully remote compatible"
                },
                "language_match": {
                    "job_languages_required": ["English"],
                    "candidate_languages": ["English - advanced", "Spanish - native"],
                    "compatible": True
                },
                "other_relevant_factors": ["Available immediately", "Led teams of 5+ engineers"],
                "overall_rationale": "Strong technical match with 87% semantic similarity..."
            }
        }


class MatcherSummary(BaseModel):
    """Summary of the matching process."""
    
    role_title: str = Field(..., description="Job title or role name")
    primary_stack_or_domain: str = Field(..., description="Main technology stack or domain")
    key_required_skills: List[str] = Field(..., description="Key required skills for the job")
    nice_to_have_skills: List[str] = Field(..., description="Nice-to-have skills")
    hard_constraints_applied: List[str] = Field(
        ...,
        description="List of hard constraints applied during search"
    )


class MatcherResponse(BaseModel):
    """Response schema for job-candidate matching."""
    
    job_id: int = Field(..., description="Job ID that was matched")
    summary: MatcherSummary = Field(..., description="Summary of the job and matching process")
    candidates: List[CandidateMatch] = Field(
        ...,
        description="List of matched candidates, ranked by match_score"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": 42,
                "summary": {
                    "role_title": "Senior Backend Engineer",
                    "primary_stack_or_domain": "Python, FastAPI, PostgreSQL",
                    "key_required_skills": ["Python", "FastAPI", "PostgreSQL", "REST APIs"],
                    "nice_to_have_skills": ["Docker", "Kubernetes", "AWS"],
                    "hard_constraints_applied": [
                        "Skills: Python, FastAPI, PostgreSQL",
                        "Min experience: 5+ years",
                        "Seniority: Senior, Lead",
                        "Location type: Remote or Hybrid"
                    ]
                },
                "candidates": [
                    {
                        "candidate_id": 123,
                        "name": "John Doe",
                        "current_role": "Senior Backend Engineer",
                        "match_score": 87.5,
                        "hybrid_similarity_score": 0.89,
                        "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
                        "missing_required_skills": ["Kubernetes"],
                        "nice_to_have_skills_covered": ["Docker"],
                        "seniority_match": "Exact",
                        "experience": {
                            "total_years_experience": 8,
                            "relevant_experience_years": 6,
                            "relevant_summary": "6 years building scalable backend systems..."
                        },
                        "location_match": {
                            "job_location_type": "Remote",
                            "candidate_location_type_preference": "Remote",
                            "compatible": True,
                            "notes": "Fully remote compatible"
                        },
                        "language_match": {
                            "job_languages_required": ["English"],
                            "candidate_languages": ["English - advanced"],
                            "compatible": True
                        },
                        "other_relevant_factors": ["Available immediately"],
                        "overall_rationale": "Strong match with 87% semantic similarity..."
                    }
                ]
            }
        }


class MatcherErrorResponse(BaseModel):
    """Error response schema."""
    
    job_id: int = Field(..., description="Job ID that was attempted")
    error: str = Field(..., description="Error message")
    candidates: List = Field(default_factory=list, description="Empty list on error")
