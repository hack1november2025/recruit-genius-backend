from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.repositories.match import MatchRepository
from app.schemas.match import MatchCreate, MatchResponse

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_match(
    match: MatchCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a candidate-job match.
    
    Note: This endpoint is deprecated. Use /api/v1/matcher/match instead for AI-powered matching.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint is deprecated. Use /api/v1/matcher/match for AI-powered matching."
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
