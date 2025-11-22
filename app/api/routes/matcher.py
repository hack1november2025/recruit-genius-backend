"""API routes for job-candidate matching."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.schemas.matcher import (
    MatcherRequest,
    MatcherResponse,
    MatcherErrorResponse,
    MatcherSummary,
    CandidateMatch,
    ExperienceInfo,
    LocationMatchInfo,
    LanguageMatchInfo
)
from app.services.matcher import MatcherService
from app.core.logging import rag_logger


router = APIRouter(prefix="/jobs", tags=["matching"])


@router.post(
    "/{job_id}/match",
    response_model=MatcherResponse,
    status_code=status.HTTP_200_OK,
    summary="Find best matching candidates for a job",
    description="""
    Performs hybrid search (semantic + metadata filtering) to find the best candidates 
    for a given job opening.
    
    The matching process:
    1. Retrieves job description, embeddings, and metadata
    2. Applies hard constraints (required skills, experience, location, etc.)
    3. Performs vector similarity search over candidate CVs
    4. Scores and ranks candidates based on multiple dimensions
    5. Returns top-k candidates with detailed match breakdown
    
    **Match Score Calculation:**
    - Semantic similarity (30%)
    - Required skills match (40%)
    - Experience alignment (15%)
    - Seniority match (10%)
    - Nice-to-have skills (5%)
    
    **Hard Constraints:**
    Candidates failing hard constraints are automatically filtered out:
    - Required skills
    - Minimum experience years
    - Seniority level
    - Language requirements
    - Location/remote type
    """
)
async def match_candidates_for_job(
    job_id: int,
    request: MatcherRequest | None = None,
    db: AsyncSession = Depends(get_db)
) -> MatcherResponse:
    """
    Find and rank the best matching candidates for a job.
    
    Args:
        job_id: Job ID to match candidates against
        request: Optional matching parameters (top_k, constraints, etc.)
        db: Database session
        
    Returns:
        Ranked list of matching candidates with detailed breakdown
        
    Raises:
        HTTPException: If job not found or matching fails
    """
    # Use defaults if no request body provided
    if request is None:
        request = MatcherRequest(job_id=job_id)
    
    # Ensure job_id matches
    request.job_id = job_id
    
    rag_logger.info(f"Matching candidates for job {job_id}")
    
    try:
        # Execute matching workflow
        matcher_service = MatcherService(db)
        result = await matcher_service.find_matches_for_job(
            job_id=request.job_id,
            top_k=request.top_k,
            hard_constraints_overrides=request.hard_constraints_overrides,
            persist_matches=request.persist_matches
        )
        
        # Check for errors
        if result.get("error"):
            error_msg = result["error"]
            if "not found" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )
        
        # Parse and validate response
        summary = MatcherSummary(**result["summary"])
        
        candidates = []
        for candidate_data in result["candidates"]:
            candidate = CandidateMatch(
                candidate_id=candidate_data["candidate_id"],
                name=candidate_data["name"],
                current_role=candidate_data["current_role"],
                match_score=candidate_data["match_score"],
                hybrid_similarity_score=candidate_data["hybrid_similarity_score"],
                matched_skills=candidate_data["matched_skills"],
                missing_required_skills=candidate_data["missing_required_skills"],
                nice_to_have_skills_covered=candidate_data["nice_to_have_skills_covered"],
                seniority_match=candidate_data["seniority_match"],
                experience=ExperienceInfo(**candidate_data["experience"]),
                location_match=LocationMatchInfo(**candidate_data["location_match"]),
                language_match=LanguageMatchInfo(**candidate_data["language_match"]),
                other_relevant_factors=candidate_data["other_relevant_factors"],
                overall_rationale=candidate_data["overall_rationale"]
            )
            candidates.append(candidate)
        
        return MatcherResponse(
            job_id=job_id,
            summary=summary,
            candidates=candidates
        )
        
    except HTTPException:
        raise
    except Exception as e:
        rag_logger.error(f"Matching failed for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching process failed: {str(e)}"
        )


@router.get(
    "/{job_id}/match",
    response_model=MatcherResponse,
    status_code=status.HTTP_200_OK,
    summary="Find matching candidates (GET method)",
    description="Alternative GET endpoint for finding matches with default parameters."
)
async def match_candidates_get(
    job_id: int,
    top_k: int = 10,
    db: AsyncSession = Depends(get_db)
) -> MatcherResponse:
    """
    GET endpoint for matching candidates with default parameters.
    
    Args:
        job_id: Job ID to match candidates against
        top_k: Maximum number of candidates to return (1-50)
        db: Database session
        
    Returns:
        Ranked list of matching candidates
    """
    request = MatcherRequest(job_id=job_id, top_k=top_k)
    return await match_candidates_for_job(job_id, request, db)
