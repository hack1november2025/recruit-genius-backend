"""LangGraph workflow for job description generation."""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import ToolNode
from app.agents.job_generator.state import JobGeneratorState
from app.agents.job_generator.nodes import call_model, route_after_agent
from app.agents.job_generator.tools import save_job_to_database
from app.core.config import get_settings
from app.core.logging import llm_logger
import psycopg


# Global checkpointer instance to keep connection alive
_checkpointer = None


async def create_job_generator_graph() -> StateGraph:
    """
    Create and compile the conversational job generator agent graph.
    
    This is a reactive agent with tool calling:
    - Agent generates/modifies job descriptions in markdown
    - Agent maintains conversation context across messages
    - Agent calls save_job_to_database tool when user approves
    - PostgreSQL checkpointer persists conversation by thread_id
    """
    
    global _checkpointer
    
    settings = get_settings()
    
    # Convert asyncpg URL to psycopg format for AsyncPostgresSaver
    # AsyncPostgresSaver uses psycopg (not asyncpg) and needs postgresql:// not postgresql+asyncpg://
    checkpoint_db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Create persistent async connection and checkpointer
    if _checkpointer is None:
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
        
        llm_logger.info("PostgreSQL async checkpointer initialized with persistent connection")
    
    # Create workflow
    workflow = StateGraph(JobGeneratorState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode([save_job_to_database]))
    
    # Define edges
    workflow.add_edge(START, "agent")
    
    # Conditional routing: agent -> tools (if tool calls) or END
    workflow.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # After tools execute, go back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile with checkpointing
    graph = workflow.compile(checkpointer=_checkpointer)
    
    llm_logger.info("Job generator graph compiled with async checkpointing")
    
    return graph






