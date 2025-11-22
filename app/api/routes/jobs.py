from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.repositories.job import JobRepository
from app.services.job_processing_service import JobProcessingService
from app.schemas.job import JobCreate, JobUpdate, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job: JobCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new job posting with automatic embedding and metadata generation."""
    repo = JobRepository(db)
    processing_service = JobProcessingService()
    
    # Create job
    new_job = await repo.create(**job.model_dump())
    
    # Process job: generate embeddings and extract metadata
    await processing_service.process_job_description(
        job_id=new_job.id,
        job_description=new_job.description,
        db=db
    )
    
    return new_job


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """List all jobs."""
    repo = JobRepository(db)
    
    if status_filter:
        from app.db.models.job import JobStatus
        try:
            job_status = JobStatus(status_filter)
            jobs = await repo.get_by_status(job_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    else:
        jobs = await repo.get_all(skip=skip, limit=limit)
    
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific job."""
    repo = JobRepository(db)
    job = await repo.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a job."""
    repo = JobRepository(db)
    
    # Filter out None values
    update_data = {k: v for k, v in job_update.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated_job = await repo.update(job_id, **update_data)
    
    if not updated_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return updated_job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a job."""
    repo = JobRepository(db)
    deleted = await repo.delete(job_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )


@router.post("/{job_id}/reprocess", status_code=status.HTTP_200_OK)
async def reprocess_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Reprocess a job to regenerate embeddings and metadata.
    
    Useful for:
    - Jobs created before processing was implemented
    - Jobs that failed processing
    - Jobs that need updated metadata/embeddings
    """
    repo = JobRepository(db)
    processing_service = JobProcessingService()
    
    # Get job
    job = await repo.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Reprocess job
    result = await processing_service.process_job_description(
        job_id=job.id,
        job_description=job.description,
        db=db
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {result.get('error')}"
        )
    
    return {
        "job_id": job_id,
        "embeddings_count": result.get("embeddings_count"),
        "metadata": result.get("metadata"),
        "message": "Job successfully reprocessed"
    }


@router.post("/batch-reprocess", status_code=status.HTTP_200_OK)
async def batch_reprocess_jobs(
    db: AsyncSession = Depends(get_db)
):
    """
    Reprocess all jobs to generate embeddings and metadata.
    
    This is useful for:
    - Initial setup when adding the processing feature
    - Bulk reprocessing after metadata schema changes
    """
    from app.db.models.job_metadata import JobMetadata
    from sqlalchemy import select, func
    
    repo = JobRepository(db)
    processing_service = JobProcessingService()
    
    # Get all jobs
    all_jobs = await repo.get_all(skip=0, limit=10000)
    
    results = {
        "total_jobs": len(all_jobs),
        "processed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": []
    }
    
    for job in all_jobs:
        try:
            # Check if already has metadata (embeddings are in LangChain now)
            result = await db.execute(
                select(func.count(JobMetadata.id)).where(JobMetadata.job_id == job.id)
            )
            metadata_count = result.scalar()
            
            # Skip if already processed (unless you want to force reprocess)
            if metadata_count > 0:
                results["skipped"] += 1
                continue
            
            # Process job
            process_result = await processing_service.process_job_description(
                job_id=job.id,
                job_description=job.description,
                db=db
            )
            
            if process_result.get("success"):
                results["processed"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "job_id": job.id,
                    "error": process_result.get("error")
                })
        
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "job_id": job.id,
                "error": str(e)
            })
    
    return results
