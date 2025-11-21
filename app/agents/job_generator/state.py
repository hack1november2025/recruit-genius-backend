"""State definition for job generator agent."""
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class JobGeneratorState(TypedDict):
    """State schema for conversational job generator agent."""
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Current generated job description (in markdown)
    job_description_markdown: str | None
    
    # Metadata about the job
    job_metadata: dict  # Can store title, department, location, etc.
