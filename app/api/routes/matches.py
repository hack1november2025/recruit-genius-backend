from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.repositories.match import MatchRepository
from app.schemas.match import MatchCreate, MatchResponse
from app.services.recruiter import RecruiterService

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_match(
    match: MatchCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a candidate-job match using AI analysis."""
    service = RecruiterService(db)
    
    try:
        result = await service.match_candidate_to_job(
            candidate_id=match.candidate_id,
            job_id=match.job_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Match creation failed: {str(e)}"
        )


@router.get("/candidate/{candidate_id}", response_model=list[MatchResponse])
async def get_matches_for_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all matches for a candidate."""
    repo = MatchRepository(db)
    matches = await repo.get_by_candidate(candidate_id)
    return matches


@router.get("/job/{job_id}", response_model=list[MatchResponse])
async def get_matches_for_job(
    job_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get top matches for a job."""
    repo = MatchRepository(db)
    matches = await repo.get_top_matches(job_id, limit=limit)
    return matches


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific match."""
    repo = MatchRepository(db)
    match = await repo.get(match_id)
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    return match
