from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class RecruiterState(TypedDict):
    """State schema for recruitment agent."""
    
    messages: Annotated[list[BaseMessage], add_messages]
    candidate_data: dict | None
    job_data: dict | None
    analysis_result: dict | None
    match_score: float | None
    recommendations: list[str]
