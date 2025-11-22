"""API routes for CV database chat interface."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.services.chat_orchestrator import ChatOrchestrator
from app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    TelegramChatRequest,
    TelegramChatResponse,
    CandidateSummary
)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/query", response_model=ChatQueryResponse)
async def process_chat_query(
    request: ChatQueryRequest,
    db: AsyncSession = Depends(get_db)
) -> ChatQueryResponse:
    """
    Process a natural language query against the CV database.
    
    This endpoint uses LangGraph's checkpointer for conversation persistence.
    Each thread_id maintains its own conversation history automatically.
    
    Features:
    - Maintains conversation context across multiple queries via thread_id
    - Returns natural language response with structured candidate data
    - Supports multi-turn conversations and query refinement
    - No need to manage sessions - just use consistent thread_id
    
    Examples:
    - "Find me senior Python developers in London"
    - "Who among them has AWS experience?"
    - "Compare the top 3 candidates"
    
    Args:
        request: Chat query request (thread_id optional - will be generated if not provided)
        db: Database session
        
    Returns:
        Chat response with answer, candidate information, and thread_id for follow-ups
    """
    orchestrator = ChatOrchestrator(db)
    return await orchestrator.process_query(request)


@router.post("/telegram", response_model=TelegramChatResponse)
async def process_telegram_query(
    request: TelegramChatRequest,
    db: AsyncSession = Depends(get_db)
) -> TelegramChatResponse:
    """
    Process a chat query from Telegram bot.
    
    This endpoint is designed for Telegram integration and:
    - Maps Telegram user ID to consistent thread_id for conversation continuity
    - Returns formatted response suitable for Telegram
    - Supports the same conversational capabilities as web UI
    
    Args:
        request: Telegram chat request
        db: Database session
        
    Returns:
        Telegram-formatted chat response
    """
    # Use Telegram user ID as thread_id for conversation continuity
    # Or use provided thread_id if user wants multiple conversations
    thread_id = request.thread_id or f"telegram_{request.telegram_user_id}"
    
    # Convert Telegram request to standard chat query
    chat_request = ChatQueryRequest(
        query=request.message,
        thread_id=thread_id,
        user_identifier=f"telegram_{request.telegram_user_id}"
    )
    
    orchestrator = ChatOrchestrator(db)
    result = await orchestrator.process_query(chat_request)
    
    # Extract candidate summaries from structured response
    candidates = []
    structured = result.structured_response
    
    if structured.get("type") == "candidates" and "candidates" in structured:
        for c in structured["candidates"]:
            candidates.append(
                CandidateSummary(
                    candidate_id=c["candidate_id"],
                    name=c["name"],
                    email=c["email"],
                    skills=c.get("skills", []),
                    experience_years=c.get("experience_years"),
                    location=c.get("location"),
                    similarity_score=c.get("similarity_score"),
                    summary=c.get("summary")
                )
            )
    
    return TelegramChatResponse(
        thread_id=result.thread_id,
        response_text=result.response_text,
        candidates=candidates
    )
