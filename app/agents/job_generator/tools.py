"""Tools for job generator agent."""
from typing import Annotated
from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.repositories.job import JobRepository
from app.services.job_processing_service import JobProcessingService
from app.core.logging import llm_logger


@tool
async def save_job_to_database(
    title: Annotated[str, "The job title"],
    description: Annotated[str, "The full job description in markdown format"],
    department: Annotated[str | None, "Department name"] = None,
    location: Annotated[str | None, "Job location"] = None,
    salary_range: Annotated[str | None, "Salary range"] = None,
) -> str:
    """
    Save the approved job description to the database.
    
    Call this tool ONLY when the user explicitly approves the job description
    (e.g., "looks good", "save it", "create the job", "that's perfect").
    
    Returns:
        Success message with job ID
    """
    try:
        async with AsyncSessionLocal() as db:
            repo = JobRepository(db)
            processing_service = JobProcessingService()
            
            # Create job
            job = await repo.create(
                title=title,
                description=description,
                department=department,
                location=location,
                salary_range=salary_range,
                status="draft",
            )
            
            llm_logger.info(f"Job created with ID: {job.id}")
            
            # Process job: generate embeddings and extract metadata
            llm_logger.info(f"Processing job {job.id} - generating embeddings and metadata")
            processing_result = await processing_service.process_job_description(
                job_id=job.id,
                job_description=description,
                db=db
            )
            
            if processing_result.get("success"):
                embeddings_count = processing_result.get("embeddings_count", 0)
                llm_logger.info(f"Job {job.id} processed successfully: {embeddings_count} embeddings created")
                return f"✅ Job successfully created with ID {job.id}! Generated {embeddings_count} embeddings and extracted metadata for hybrid search."
            else:
                llm_logger.warning(f"Job {job.id} created but processing failed: {processing_result.get('error')}")
                return f"⚠️ Job created with ID {job.id}, but metadata extraction had issues. The job is saved but may need reprocessing."
    
    except Exception as e:
        llm_logger.error(f"Failed to save job: {str(e)}")
        return f"❌ Failed to save job: {str(e)}"
