"""LangGraph workflow for the matcher agent."""
from typing import Callable
from langgraph.graph import StateGraph, START, END
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.matcher.state import MatcherState
from app.agents.matcher.nodes import (
    retrieve_job_node,
    rag_search_node,
    calculate_metrics_node,
    score_candidates_node
)
from app.core.logging import rag_logger


def create_db_node(node_func: Callable, db: AsyncSession) -> Callable:
    """Wrapper to inject database session into node functions."""
    async def wrapped(state: MatcherState) -> dict:
        return await node_func(state, db)
    return wrapped


def create_matcher_graph(db: AsyncSession) -> StateGraph:
    """
    Create and compile the matcher agent graph.
    
    The workflow (RAG-first approach):
    1. START -> retrieve_job: Fetch job data, embeddings, and metadata
    2. retrieve_job -> rag_search: Perform vector similarity search (no filters, wide net)
    3. rag_search -> calculate_metrics: Calculate 8 comprehensive metrics for each CV
    4. calculate_metrics -> score_candidates: Rank candidates by composite scores
    5. score_candidates -> END: Return final results with all metrics
    
    Error handling:
    - If error occurs at any step, subsequent steps are skipped
    - Error information is preserved in state
    
    Args:
        db: Database session for data access
        
    Returns:
        Compiled StateGraph ready for execution
    """
    workflow = StateGraph(MatcherState)
    
    # Add nodes with database injection where needed
    workflow.add_node("retrieve_job", create_db_node(retrieve_job_node, db))
    workflow.add_node("rag_search", create_db_node(rag_search_node, db))
    workflow.add_node("calculate_metrics", create_db_node(calculate_metrics_node, db))
    workflow.add_node("score_candidates", score_candidates_node)
    
    # Define edges
    workflow.add_edge(START, "retrieve_job")
    
    # Conditional edge: if error, skip to end
    def check_error(state: MatcherState) -> str:
        """Route based on error state."""
        if state.get("error"):
            return "end"
        return "continue"
    
    workflow.add_conditional_edges(
        "retrieve_job",
        check_error,
        {
            "continue": "rag_search",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "rag_search",
        check_error,
        {
            "continue": "calculate_metrics",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "calculate_metrics",
        check_error,
        {
            "continue": "score_candidates",
            "end": END
        }
    )
    
    workflow.add_edge("score_candidates", END)
    
    # Compile the graph
    compiled_graph = workflow.compile()
    
    rag_logger.info("Matcher agent graph compiled successfully (RAG-first with metrics)")
    
    return compiled_graph


async def run_matcher_workflow(
    job_id: int,
    db: AsyncSession,
    top_k: int = 10,
    hard_constraints_overrides: dict | None = None
) -> dict:
    """
    Execute the matcher workflow for a given job.
    
    Args:
        job_id: Job ID to match candidates against
        db: Database session
        top_k: Maximum number of candidates to return
        hard_constraints_overrides: Optional additional constraints
        
    Returns:
        Dictionary with match results or error information
    """
    # Create graph
    graph = create_matcher_graph(db)
    
    # Prepare initial state
    initial_state: MatcherState = {
        "job_id": job_id,
        "top_k": top_k,
        "hard_constraints_overrides": hard_constraints_overrides or {},
        "job_data": None,
        "job_text": None,
        "job_embedding": None,
        "job_metadata": None,
        "metadata_filters": {},
        "candidate_results": [],
        "final_matches": [],
        "summary": None,
        "error": None,
    }
    
    try:
        # Execute workflow
        rag_logger.info(f"Starting matcher workflow for job_id={job_id}, top_k={top_k}")
        result = await graph.ainvoke(initial_state)
        
        if result.get("error"):
            rag_logger.error(f"Matcher workflow failed: {result['error']}")
            return {
                "job_id": job_id,
                "error": result["error"],
                "candidates": []
            }
        
        # Format output
        output = {
            "job_id": job_id,
            "summary": result.get("summary", {}),
            "candidates": result.get("final_matches", [])
        }
        
        rag_logger.info(f"Matcher workflow completed: {len(output['candidates'])} candidates found")
        return output
        
    except Exception as e:
        rag_logger.error(f"Matcher workflow exception: {str(e)}")
        return {
            "job_id": job_id,
            "error": f"Workflow execution failed: {str(e)}",
            "candidates": []
        }
