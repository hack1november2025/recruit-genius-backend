"""Repository for CV operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.cv import CV
from app.repositories.base import BaseRepository


class CVRepository(BaseRepository[CV]):
    """Repository for CV operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(CV, db)
    
    async def get_by_candidate(self, candidate_id: int) -> list[CV]:
        """Get all CVs for a specific candidate."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.candidate_id == candidate_id)
            .order_by(self.model.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_latest_by_candidate(self, candidate_id: int) -> CV | None:
        """Get the most recent CV for a candidate."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.candidate_id == candidate_id)
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
