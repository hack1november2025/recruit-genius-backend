"""Graph definition for CV Parser agent."""
from langgraph.graph import StateGraph, START, END
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.cv_parser.state import CVParserState
from app.agents.cv_parser.nodes import (
    extract_text_node,
    detect_and_translate_node,
    extract_metadata_node,
    create_embeddings_node
)
from app.core.logging import llm_logger


def create_cv_parser_graph(db: AsyncSession):
    """Create and compile CV parser agent graph."""
    
    workflow = StateGraph(CVParserState)
    
    # Create wrapper for embeddings node that includes db session
    async def embeddings_with_db(state: CVParserState) -> dict:
        return await create_embeddings_node(state, db)
    
    # Add nodes
    workflow.add_node("extract_text", extract_text_node)
    workflow.add_node("translate", detect_and_translate_node)
    workflow.add_node("extract_metadata", extract_metadata_node)
    workflow.add_node("create_embeddings", embeddings_with_db)
    
    # Define linear workflow
    workflow.add_edge(START, "extract_text")
    workflow.add_edge("extract_text", "translate")
    workflow.add_edge("translate", "extract_metadata")
    workflow.add_edge("extract_metadata", "create_embeddings")
    workflow.add_edge("create_embeddings", END)
    
    # Compile without checkpointing (single-shot processing)
    graph = workflow.compile()
    
    llm_logger.info("CV Parser graph compiled")
    return graph
