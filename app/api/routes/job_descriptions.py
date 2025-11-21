"""API routes for conversational AI-powered job description generation."""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.job_generator import JobGeneratorService
import uuid

router = APIRouter(prefix="/job-descriptions", tags=["job-descriptions"])

# Initialize service once
job_service = JobGeneratorService()


class ChatRequest(BaseModel):
    """Request for conversational job generation."""
    message: str


class ChatResponse(BaseModel):
    """Response from conversational job generation."""
    response: str
    thread_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat_job_description(
    request: ChatRequest,
    thread_id: str = Query(None, description="Conversation thread ID for persistence")
):
    """
    Chat with the job description generator agent.
    
    This conversational endpoint allows you to:
    - Create job descriptions from simple text prompts
    - Request modifications to existing descriptions
    - Maintain context across multiple messages
    - Save approved descriptions to the database via agent tool
    
    The agent returns only markdown-formatted job descriptions.
    
    Args:
        request: User message (e.g., "Create job for senior Python developer")
        thread_id: Optional thread ID to continue existing conversation
        
    Returns:
        Markdown job description and thread_id for future messages
        
    Examples:
        ```
        # Start new conversation
        POST /api/v1/job-descriptions/chat
        {"message": "Create job posting for senior backend engineer with 5 years Python"}
        
        # Continue conversation with modifications
        POST /api/v1/job-descriptions/chat?thread_id=abc123
        {"message": "Make it more friendly and emphasize remote work"}
        
        # Save to database
        POST /api/v1/job-descriptions/chat?thread_id=abc123
        {"message": "Save this job with title 'Senior Backend Engineer'"}
        ```
    """
    # Generate thread_id if not provided
    if not thread_id:
        thread_id = f"job_{uuid.uuid4().hex[:12]}"
    
    # Get response from agent
    response = await job_service.chat(request.message, thread_id)
    
    return ChatResponse(
        response=response,
        thread_id=thread_id
    )


@router.post("/chat/stream")
async def stream_chat_job_description(
    request: ChatRequest,
    thread_id: str = Query(None, description="Conversation thread ID")
):
    """
    Stream chat responses from the job description generator.
    
    Same functionality as /chat but returns streaming response.
    Useful for real-time UI updates as the agent generates content.
    
    Returns:
        Server-Sent Events stream with markdown chunks
    """
    if not thread_id:
        thread_id = f"job_{uuid.uuid4().hex[:12]}"
    
    async def event_stream():
        # Send thread_id first
        yield f"data: {{'thread_id': '{thread_id}'}}\n\n"
        
        # Stream agent responses
        async for chunk in job_service.stream_chat(request.message, thread_id):
            yield f"data: {{'chunk': {repr(chunk)}}}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

