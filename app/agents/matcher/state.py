"""State schema for the matcher agent."""
from typing import TypedDict, List, Dict, Any


class MatcherState(TypedDict):
    """State schema for job-candidate matching agent."""
    
    # Input
    job_id: int
    top_k: int
    hard_constraints_overrides: Dict[str, Any]
    
    # Job information
    job_data: Dict[str, Any] | None
    job_text: str | None
    job_metadata: Dict[str, Any] | None
    
    # Metadata filters (derived from job + overrides)
    metadata_filters: Dict[str, Any]
    
    # Search results
    candidate_results: List[Dict[str, Any]]
    
    # Scored and ranked candidates
    final_matches: List[Dict[str, Any]]
    
    # Summary
    summary: Dict[str, Any] | None
    
    # Error handling
    error: str | None
