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
    status_code=status.HTTP_200_OK,
    summary="Find best matching candidates for a job",
    description="""
    Performs RAG-first search with comprehensive metrics calculation to find the best candidates.
    
    The matching process:
    1. Retrieves job description, embeddings, and metadata
    2. Performs vector similarity search (RAG-only, no upfront filtering)
    3. Calculates 8 comprehensive metrics for each candidate
    4. Ranks candidates by composite score
    5. Returns top-k candidates with all metrics
    
    **Metrics Calculated (8):**
    - Core Fit: Skills match, Experience relevance, Education fit
    - Quality: Achievement impact, Keyword density
    - Risk/Confidence: Employment gaps, Readability, AI confidence
    - Composite score (weighted combination)
    """
)
async def match_candidates_for_job(
    job_id: int,
    top_k: int = 10,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Find and rank the best matching candidates for a job.
    
    Args:
        job_id: Job ID to match candidates against
        top_k: Maximum number of candidates to return
        db: Database session
        
    Returns:
        Ranked list of matching candidates with detailed metrics
        
    Raises:
        HTTPException: If job not found or matching fails
    """
    rag_logger.info(f"Matching candidates for job {job_id}")
    
    try:
        # Execute matching workflow
        matcher_service = MatcherService(db)
        result = await matcher_service.find_matches_for_job(
            job_id=job_id,
            top_k=top_k,
            hard_constraints_overrides=None,
            persist_matches=True
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
        
        # Return raw result with all metrics
        return result
        
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
    status_code=status.HTTP_200_OK,
    summary="Find matching candidates (GET method)",
    description="Alternative GET endpoint for finding matches with default parameters."
)
async def match_candidates_get(
    job_id: int,
    top_k: int = 10,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    GET endpoint for matching candidates with default parameters.
    
    Args:
        job_id: Job ID to match candidates against
        top_k: Maximum number of candidates to return (1-50)
        db: Database session
        
    Returns:
        Ranked list of matching candidates with metrics
    """
    return await match_candidates_for_job(job_id, top_k, db)
