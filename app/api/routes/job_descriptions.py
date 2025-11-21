"""API routes for AI-powered job description generation."""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from app.schemas.job_description import (
    JobDescriptionGenerateRequest,
    JobDescriptionResponse,
)
from app.services.job_generator import JobGeneratorService
import json

router = APIRouter(prefix="/job-descriptions", tags=["job-descriptions"])


@router.post("/generate", response_model=JobDescriptionResponse)
async def generate_job_description(
    request: JobDescriptionGenerateRequest,
    stream: bool = Query(False, description="Enable streaming response")
):
    """
    Generate a complete job description from a brief description.
    
    This endpoint uses AI to expand a short job summary into a full,
    professional job posting with responsibilities, qualifications, and benefits.
    
    Args:
        request: Brief description and optional parameters (department, location, tone)
        stream: If True, returns streaming response. If False, returns complete response.
        
    Returns:
        Complete job description with all sections, or streaming updates if stream=True
        
    Example:
        ```
        POST /api/v1/job-descriptions/generate
        {
            "brief_description": "Senior backend developer with Python and AWS experience",
            "department": "Engineering",
            "location": "Remote",
            "tone": "friendly"
        }
        ```
    """
    service = JobGeneratorService()
    
    if stream:
        # Streaming response
        async def event_stream():
            async for event in service.generate_description_stream(request):
                # Send as Server-Sent Events format
                yield f"data: {json.dumps(event)}\n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )
    else:
        # Regular response
        result = await service.generate_description(request)
        return result
