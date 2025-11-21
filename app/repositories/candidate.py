from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.db.models.candidate import Candidate, CandidateStatus


class CandidateRepository(BaseRepository[Candidate]):
    """Repository for candidate operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Candidate, db)
    
    async def get_by_email(self, email: str) -> Candidate | None:
        """Get candidate by email."""
        result = await self.db.execute(
            select(self.model).where(self.model.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_status(self, status: CandidateStatus) -> list[Candidate]:
        """Get candidates by status."""
        result = await self.db.execute(
            select(self.model).where(self.model.status == status)
        )
        return list(result.scalars().all())
