"""LangGraph workflow for CV Chat agent."""
from typing import Callable
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.cv_chat.state import CVChatState
from app.agents.cv_chat.nodes import (
    understand_query_node,
    retrieve_candidates_node,
    generate_response_node
)
from app.core.config import get_settings
from app.core.logging import rag_logger
import psycopg


# Global checkpointer instance to keep connection alive
_checkpointer = None


def create_db_node(node_func: Callable, db: AsyncSession) -> Callable:
    """Wrapper to inject database session into node functions."""
    async def wrapped(state: CVChatState) -> dict:
        return await node_func(state, db)
    return wrapped


async def get_checkpointer() -> AsyncPostgresSaver:
    """Get or create the global checkpointer instance."""
    global _checkpointer
    
    if _checkpointer is None:
        settings = get_settings()
        # Convert asyncpg URL to psycopg format
        checkpoint_db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        # Create async connection
        conn = await psycopg.AsyncConnection.connect(
            checkpoint_db_url,
            autocommit=True,
            prepare_threshold=0,
            row_factory=psycopg.rows.dict_row
        )
        
        # Create checkpointer with persistent connection
        _checkpointer = AsyncPostgresSaver(conn)
        await _checkpointer.setup()
        
        rag_logger.info("CV Chat: PostgreSQL async checkpointer initialized")
    
    return _checkpointer


def create_cv_chat_graph(db: AsyncSession) -> StateGraph:
    """
    Create the CV chat agent graph (NOT compiled - compilation happens with checkpointer).
    
    Workflow:
    1. START -> understand_query: Analyze user query and extract intent/parameters
    2. understand_query -> check_clarification: Determine if clarification needed
       - If needs clarification -> generate_response (with clarification message)
       - If clear -> retrieve_candidates
    3. retrieve_candidates -> generate_response: Get candidates and generate response
    4. generate_response -> END: Return final response
    
    The agent maintains conversation context through the messages list,
    enabling multi-turn conversations and query refinement.
    
    Args:
        db: Database session for data access
        
    Returns:
        StateGraph ready for compilation with checkpointer
    """
    workflow = StateGraph(CVChatState)
    
    # Add nodes with database injection
    workflow.add_node("understand_query", create_db_node(understand_query_node, db))
    workflow.add_node("retrieve_candidates", create_db_node(retrieve_candidates_node, db))
    workflow.add_node("generate_response", create_db_node(generate_response_node, db))
    
    # Define edges
    workflow.add_edge(START, "understand_query")
    
    # Conditional routing after query understanding
    def route_after_understanding(state: CVChatState) -> str:
        """Route based on whether clarification is needed or error occurred."""
        rag_logger.info(f"Routing decision - Intent: {state.get('query_intent')}, Error: {state.get('error')}, Clarification: {state.get('requires_clarification')}")
        
        if state.get("error"):
            rag_logger.info("Routing to generate_response (error)")
            return "generate_response"
        if state.get("requires_clarification"):
            rag_logger.info("Routing to generate_response (clarification needed)")
            return "generate_response"
        if state.get("query_intent") == "clarify":
            rag_logger.info("Routing to generate_response (clarify intent)")
            return "generate_response"
        
        rag_logger.info("Routing to retrieve_candidates")
        return "retrieve_candidates"
    
    workflow.add_conditional_edges(
        "understand_query",
        route_after_understanding,
        {
            "retrieve_candidates": "retrieve_candidates",
            "generate_response": "generate_response"
        }
    )
    
    # After retrieval, always generate response
    workflow.add_edge("retrieve_candidates", "generate_response")
    workflow.add_edge("generate_response", END)
    
    rag_logger.info("CV Chat agent graph structure created")
    
    return workflow


async def run_cv_chat_workflow(
    user_query: str,
    thread_id: str,
    user_identifier: str,
    db: AsyncSession,
) -> dict:
    """
    Execute the CV chat workflow for a user query.
    
    Uses LangGraph's checkpointer to maintain conversation history per thread_id.
    No need for separate session tables - checkpointer handles everything.
    
    Args:
        user_query: User's natural language query
        thread_id: Unique thread ID for conversation persistence
        user_identifier: User identifier (for logging/analytics)
        db: Database session for candidate retrieval
        
    Returns:
        Dictionary with response text, structured data, and updated state
    """
    # Get checkpointer
    checkpointer = await get_checkpointer()
    
    # Create graph structure
    workflow = create_cv_chat_graph(db)
    
    # Compile with checkpointer (only compilation happens here)
    compiled_graph = workflow.compile(checkpointer=checkpointer)
    
    rag_logger.info("CV Chat agent graph compiled with checkpointer")
    
    # Configuration for thread-based checkpointing
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    # Get existing state from checkpointer (if any)
    # This loads the conversation history automatically
    existing_state = await compiled_graph.aget_state(config)
    
    # Get existing messages from checkpointed state
    existing_messages = existing_state.values.get("messages", []) if existing_state.values else []
    
    # Prepare initial state (merges with existing via checkpointer)
    from langchain_core.messages import HumanMessage
    
    initial_state: CVChatState = {
        "messages": existing_messages + [HumanMessage(content=user_query)],
        "user_identifier": user_identifier,
        "user_query": user_query,
        "query_intent": None,
        "search_params": {},
        "query_embedding": None,
        "candidate_results": [],
        "candidate_ids_in_context": existing_state.values.get("candidate_ids_in_context", []) if existing_state.values else [],
        "response_text": None,
        "structured_response": None,
        "requires_clarification": False,
        "clarification_message": None,
        "error": None,
    }
    
    try:
        rag_logger.info(f"Starting CV chat workflow for thread {thread_id}")
        result = await compiled_graph.ainvoke(initial_state, config=config)
        
        # Extract key results
        output = {
            "thread_id": thread_id,
            "response_text": result.get("response_text", ""),
            "structured_response": result.get("structured_response", {}),
            "candidate_ids": result.get("candidate_ids_in_context", []),
            "messages": result.get("messages", []),
            "error": result.get("error"),
        }
        
        rag_logger.info(f"CV chat workflow completed for thread {thread_id}")
        return output
        
    except Exception as e:
        rag_logger.error(f"CV chat workflow exception: {str(e)}")
        return {
            "thread_id": thread_id,
            "response_text": "I encountered an error processing your request. Please try again.",
            "structured_response": {
                "type": "error",
                "message": str(e)
            },
            "candidate_ids": [],
            "messages": [],
            "error": str(e)
        }
