"""LangGraph workflow for CV Chat agent using agentic RAG pattern."""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import create_react_agent
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_openai import ChatOpenAI
from app.agents.cv_chat.state import CVChatState
from app.agents.cv_chat.tools import get_cv_chat_tools
from app.core.config import get_settings
from app.core.logging import rag_logger
import psycopg


# Global checkpointer instance to keep connection alive
_checkpointer = None


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


def create_cv_chat_agent():
    """
    Create agentic RAG agent using LangChain's react pattern.
    
    This follows LangChain's recommended agentic RAG approach where:
    - The LLM decides when to use retrieval tools
    - Tools are simple, focused functions decorated with @tool
    - The agent reasons step-by-step and calls tools as needed
    
    Returns:
        Agent executor (not yet compiled with checkpointer)
    """
    settings = get_settings()
    
    # System prompt for the agent
    system_prompt = """You are an expert HR assistant with access to a comprehensive CV database.

Your role is to help HR personnel find and analyze candidate profiles using natural language.

**Available Tools:**
- search_candidates: Use this to find candidates based on skills, experience, job descriptions, or any natural language query
  
**Guidelines:**
- When a user asks about candidates, ALWAYS use the search_candidates tool
- Be conversational and professional
- Summarize candidate information clearly
- If no candidates match, suggest alternative search approaches
- Maintain context from the conversation history
- Provide actionable insights about candidates

**Examples:**
User: "Find me Java developers"
Action: Call search_candidates with query="Java developers"

User: "Show me senior Python engineers with 5+ years"
Action: Call search_candidates with query="senior Python engineer 5 years experience"

User: "Looking for data scientists in London"
Action: Call search_candidates with query="data scientist London"

Always call the search tool first before responding about candidates.
"""
    
    # Create LLM with better model for reasoning
    llm = ChatOpenAI(
        model=settings.llm_rag_model,
        temperature=0,
        openai_api_key=settings.openai_api_key
    )
    
    # Get tools for the agent
    tools = get_cv_chat_tools()
    
    rag_logger.info(f"Creating CV chat agent with {len(tools)} tools")
    
    # Create agent using LangChain's react pattern
    # The agent will automatically handle tool calling and reasoning
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )
    
    return agent


async def run_cv_chat_workflow(
    user_query: str,
    thread_id: str,
    db: AsyncSession,  # noqa: ARG001 - kept for API compatibility
) -> dict:
    """
    Execute the CV chat workflow using agentic RAG.
    
    The agent decides when to use retrieval tools based on the query.
    LangGraph's checkpointer maintains conversation history automatically.
    
    Args:
        user_query: User's natural language query
        thread_id: Unique thread ID for conversation persistence
        db: Database session (for future use, currently tools access DB directly)
        
    Returns:
        Dictionary with response text and metadata
    """
    try:
        # Get checkpointer
        await get_checkpointer()
        
        # Create agent (returns already compiled graph)
        agent = create_cv_chat_agent()
        
        # Configuration for thread-based checkpointing
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Prepare messages for the agent
        from langchain_core.messages import HumanMessage
        
        input_messages = {"messages": [HumanMessage(content=user_query)]}
        
        rag_logger.info(f"Invoking CV chat agent for thread {thread_id}, query: {user_query[:100]}")
        
        # Invoke the agent
        result = await agent.ainvoke(input_messages, config=config)
        
        # Extract response from agent messages
        messages = result.get("messages", [])
        last_message = messages[-1] if messages else None
        
        response_text = last_message.content if last_message else "I couldn't process your request."
        
        rag_logger.info(f"CV chat agent completed for thread {thread_id}")
        
        return {
            "thread_id": thread_id,
            "response_text": response_text,
            "messages": messages,
            "structured_response": {
                "type": "chat_response",
                "agent_used_tools": any(hasattr(msg, "tool_calls") and msg.tool_calls for msg in messages)
            },
            "error": None
        }
        
    except Exception as e:
        rag_logger.error(f"CV chat workflow exception: {str(e)}", exc_info=True)
        return {
            "thread_id": thread_id,
            "response_text": "I encountered an error processing your request. Please try again.",
            "structured_response": {
                "type": "error",
                "message": str(e)
            },
            "error": str(e)
        }
