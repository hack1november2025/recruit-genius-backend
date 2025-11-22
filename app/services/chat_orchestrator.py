"""Chat orchestrator service for managing CV database conversations."""
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.cv_chat.graph import run_cv_chat_workflow
from app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
)
from app.core.logging import rag_logger
import uuid


class ChatOrchestrator:
    """
    Service to orchestrate CV chat agent execution.
    
    This service uses LangGraph's built-in checkpointer for conversation persistence.
    The checkpointer handles all conversation state and history automatically per thread_id.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def process_query(self, request: ChatQueryRequest) -> ChatQueryResponse:
        """
        Process a user query through the CV chat agent.
        
        This method:
        1. Generates or uses provided thread_id
        2. Executes the CV chat agent workflow (checkpointer loads history)
        3. Returns response (checkpointer saves state automatically)
        
        Args:
            request: Chat query request with optional thread_id
            
        Returns:
            Chat response with answer and candidate data
        """
        try:
            # Use provided thread_id or generate new one
            thread_id = request.thread_id or f"chat_{uuid.uuid4().hex[:12]}"
            
            rag_logger.info(f"Processing query for thread {thread_id}")
            
            # Execute CV chat workflow
            # Checkpointer automatically loads conversation history for this thread
            workflow_result = await run_cv_chat_workflow(
                user_query=request.query,
                thread_id=thread_id,
                db=self.db
            )
            
            rag_logger.info(f"Query processed successfully for thread {thread_id}")
            
            return ChatQueryResponse(
                thread_id=thread_id,
                response_text=workflow_result["response_text"],
                structured_response=workflow_result.get("structured_response", {}),
                candidate_ids=[],
                error=workflow_result.get("error")
            )
            
        except Exception as e:
            rag_logger.error(f"Error processing chat query: {str(e)}")
            
            # Generate thread_id for error response if needed
            thread_id = request.thread_id or f"chat_{uuid.uuid4().hex[:12]}"
            
            return ChatQueryResponse(
                thread_id=thread_id,
                response_text="I encountered an error processing your request. Please try again.",
                structured_response={
                    "type": "error",
                    "message": str(e)
                },
                candidate_ids=[],
                error=str(e)
            )
