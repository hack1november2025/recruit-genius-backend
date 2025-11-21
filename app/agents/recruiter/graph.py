from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.agents.recruiter.state import RecruiterState
from app.agents.recruiter.nodes import (
    analyze_resume,
    match_candidate_to_job,
    generate_recommendations,
)


def create_recruiter_graph(checkpointer: AsyncPostgresSaver | None = None):
    """Create and compile recruitment agent graph."""
    
    workflow = StateGraph(RecruiterState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_resume)
    workflow.add_node("match", match_candidate_to_job)
    workflow.add_node("recommend", generate_recommendations)
    
    # Define edges
    workflow.add_edge(START, "analyze")
    workflow.add_edge("analyze", "match")
    workflow.add_edge("match", "recommend")
    workflow.add_edge("recommend", END)
    
    # Compile with optional checkpointing
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    return workflow.compile()
