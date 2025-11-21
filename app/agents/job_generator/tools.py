"""Tools for job generator agent."""
from typing import Annotated
from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.repositories.job import JobRepository
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
            
            return f"✅ Job successfully created with ID {job.id}! The job posting is now saved as a draft and ready for review."
    
    except Exception as e:
        llm_logger.error(f"Failed to save job: {str(e)}")
        return f"❌ Failed to save job: {str(e)}"
