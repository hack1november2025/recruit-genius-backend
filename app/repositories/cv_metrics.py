"""Repository for CV metrics persistence."""
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cv_metrics import CVMetrics
from app.repositories.base import BaseRepository


class CVMetricsRepository(BaseRepository[CVMetrics]):
    """Repository for CV metrics operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(CVMetrics, db)
    
    async def get_by_cv_id(self, cv_id: int) -> List[CVMetrics]:
        """Get all metrics for a specific CV across different jobs."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.cv_id == cv_id)
            .order_by(self.model.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_job_id(self, job_id: int) -> List[CVMetrics]:
        """Get all metrics for a specific job across different CVs."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.job_id == job_id)
            .order_by(self.model.composite_score.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_cv_and_job(
        self,
        cv_id: int,
        job_id: int
    ) -> CVMetrics | None:
        """Get metrics for a specific CV-job pair."""
        result = await self.db.execute(
            select(self.model)
            .where(
                self.model.cv_id == cv_id,
                self.model.job_id == job_id
            )
        )
        return result.scalar_one_or_none()
    
    async def upsert_metrics(
        self,
        cv_id: int,
        job_id: int,
        metrics_data: dict
    ) -> CVMetrics:
        """
        Create or update metrics for a CV-job pair.
        
        Args:
            cv_id: CV identifier
            job_id: Job identifier
            metrics_data: Dictionary with all metric scores and details
            
        Returns:
            Created or updated CVMetrics instance
        """
        # Check if metrics already exist
        existing = await self.get_by_cv_and_job(cv_id, job_id)
        
        if existing:
            # Update existing metrics
            for key, value in metrics_data.items():
                setattr(existing, key, value)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new metrics
            return await self.create(
                cv_id=cv_id,
                job_id=job_id,
                **metrics_data
            )
    
    async def get_top_candidates(
        self,
        job_id: int,
        min_composite_score: float = 0.0,
        limit: int = 50
    ) -> List[CVMetrics]:
        """
        Get top-scoring CVs for a job.
        
        Args:
            job_id: Job identifier
            min_composite_score: Minimum composite score threshold
            limit: Maximum number of results
            
        Returns:
            List of CVMetrics ordered by composite score
        """
        result = await self.db.execute(
            select(self.model)
            .where(
                self.model.job_id == job_id,
                self.model.composite_score >= min_composite_score
            )
            .order_by(self.model.composite_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def delete_by_job_id(self, job_id: int) -> int:
        """Delete all metrics for a job. Returns count of deleted records."""
        metrics = await self.get_by_job_id(job_id)
        count = len(metrics)
        
        for metric in metrics:
            await self.db.delete(metric)
        
        await self.db.commit()
        return count
