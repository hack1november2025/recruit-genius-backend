from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.db.models.job import Job, JobStatus


class JobRepository(BaseRepository[Job]):
    """Repository for job operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Job, db)
    
    async def get_by_status(self, status: JobStatus) -> list[Job]:
        """Get jobs by status."""
        result = await self.db.execute(
            select(self.model).where(self.model.status == status)
        )
        return list(result.scalars().all())
    
    async def get_open_jobs(self) -> list[Job]:
        """Get all open job postings."""
        return await self.get_by_status(JobStatus.OPEN)
