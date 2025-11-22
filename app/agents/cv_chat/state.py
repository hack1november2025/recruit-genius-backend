"""State schema for the CV Chat agent."""
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class CVChatState(TypedDict):
    """
    State schema for CV database conversational chat agent.
    
    This agent enables natural language querying of the CV database with:
    - Contextual conversation history (managed by LangGraph checkpointer)
    - Multi-turn query refinement
    - Candidate retrieval and comparison
    - Filtering and summarization
    
    Note: No session_id needed - LangGraph's checkpointer handles persistence via thread_id
    """
    
    # Conversation context (persisted by checkpointer)
    messages: Annotated[list[BaseMessage], add_messages]
    user_identifier: str  # Telegram user ID, authenticated user ID, etc.
    
    # Current query processing
    user_query: str
    query_intent: str | None  # 'search', 'filter', 'compare', 'detail', 'clarify'
    
    # Search parameters extracted from conversation
    search_params: Dict[str, Any]  # Skills, experience, location, etc.
    query_embedding: List[float] | None
    
    # Retrieved candidates
    candidate_results: List[Dict[str, Any]]
    candidate_ids_in_context: List[int]  # Candidates mentioned in conversation (persisted)
    
    # Response generation
    response_text: str | None
    structured_response: Dict[str, Any] | None  # For UI rendering
    
    # Conversation state
    requires_clarification: bool
    clarification_message: str | None
    
    # Error handling
    error: str | None
