"""LangGraph workflow for job description generation."""
from langgraph.graph import StateGraph, START, END
from app.agents.job_generator.state import JobGeneratorState
from app.agents.job_generator import nodes


def create_job_generator_graph():
    """Create and compile job generator agent graph."""
    
    workflow = StateGraph(JobGeneratorState)
    
    # Add nodes
    workflow.add_node("analyze", nodes.analyze_brief)
    workflow.add_node("title", nodes.generate_title)
    workflow.add_node("responsibilities", nodes.generate_responsibilities)
    workflow.add_node("qualifications", nodes.generate_qualifications)
    workflow.add_node("benefits", nodes.generate_benefits)
    workflow.add_node("inclusivity", nodes.check_inclusivity)
    workflow.add_node("format", nodes.format_output)
    
    # Define flow
    workflow.add_edge(START, "analyze")
    workflow.add_edge("analyze", "title")
    workflow.add_edge("title", "responsibilities")
    workflow.add_edge("responsibilities", "qualifications")
    workflow.add_edge("qualifications", "benefits")
    workflow.add_edge("benefits", "inclusivity")
    workflow.add_edge("inclusivity", "format")
    workflow.add_edge("format", END)
    
    # Compile
    return workflow.compile()
