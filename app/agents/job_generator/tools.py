"""Tools for job generator agent."""
from typing import Annotated
from langchain_core.tools import tool
from app.core.logging import llm_logger
import asyncio


async def _save_job_impl(
    title: str,
    description: str,
    department: str | None = None,
    location: str | None = None,
    salary_range: str | None = None,
) -> str:
    """
    Async implementation that properly manages its own database connection.
    
    Creates a fresh async session to avoid conflicts with LangGraph's
    psycopg connection context.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from app.core.config import get_settings
    from app.repositories.job import JobRepository
    from app.services.job_processing_service import JobProcessingService
    
    settings = get_settings()
    
    try:
        # Create a fresh engine and session for this operation
        # This ensures we're not sharing async context with LangGraph
        engine = create_async_engine(
            settings.database_url,
            pool_size=1,
            max_overflow=0,
        )
        
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        async with async_session_maker() as db:
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
            
            # Capture job ID before session closes
            job_id = job.id
            
            llm_logger.info(f"Job created with ID: {job_id}")
            
            # Process job: generate embeddings and extract metadata
            llm_logger.info(f"Processing job {job_id} - generating embeddings and metadata")
            processing_result = await processing_service.process_job_description(
                job_id=job_id,
                job_description=description,
                db=db
            )
            
            if processing_result.get("success"):
                embeddings_count = processing_result.get("embeddings_count", 0)
                llm_logger.info(f"Job {job_id} processed successfully: {embeddings_count} embeddings created")
                result = f"✅ Job successfully created with ID {job_id}! Generated {embeddings_count} embeddings and extracted metadata for semantic search."
            else:
                llm_logger.warning(f"Job {job_id} created but processing failed: {processing_result.get('error')}")
                result = f"⚠️ Job created with ID {job_id}, but metadata extraction had issues. The job is saved but may need reprocessing."
        
        # Clean up engine
        await engine.dispose()
        
        return result
    
    except Exception as e:
        llm_logger.error(f"Failed to save job: {str(e)}", exc_info=True)
        return f"❌ Failed to save job: {str(e)}"


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
    # Call implementation directly - it manages its own engine/connection
    return await _save_job_impl(title, description, department, location, salary_range)
