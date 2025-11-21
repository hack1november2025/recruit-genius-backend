"""State definition for job generator agent."""
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class JobGeneratorState(TypedDict):
    """State schema for job generator agent."""
    messages: Annotated[list[BaseMessage], add_messages]
    brief_description: str
    department: str | None
    location: str | None
    employment_type: str | None
    salary_range: str | None
    tone: str  # formal, friendly, inclusive
    
    # Generated content
    job_title: str | None
    full_description: str | None
    responsibilities: list[str]
    required_qualifications: list[str]
    preferred_qualifications: list[str]
    benefits: list[str]
    
    # Quality checks
    inclusivity_score: float
    flagged_terms: list[str]
    
    # Control
    needs_regeneration: bool
