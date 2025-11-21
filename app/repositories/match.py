from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.db.models.match import Match


class MatchRepository(BaseRepository[Match]):
    """Repository for match operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Match, db)
    
    async def get_by_candidate(self, candidate_id: int) -> list[Match]:
        """Get all matches for a candidate."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.candidate_id == candidate_id)
            .order_by(self.model.match_score.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_job(self, job_id: int) -> list[Match]:
        """Get all matches for a job."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.job_id == job_id)
            .order_by(self.model.match_score.desc())
        )
        return list(result.scalars().all())
    
    async def get_top_matches(self, job_id: int, limit: int = 10) -> list[Match]:
        """Get top N matches for a job."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.job_id == job_id)
            .order_by(self.model.match_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
