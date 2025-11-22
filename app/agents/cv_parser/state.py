"""State definition for CV Parser agent."""
from typing import TypedDict


class CVParserState(TypedDict):
    """State schema for CV parser agent."""
    
    # Input
    file_path: str
    candidate_id: int
    
    # Extracted text
    raw_text: str | None
    original_language: str | None
    translated_text: str | None
    
    # Metadata
    structured_metadata: dict | None
    
    # Embeddings
    embeddings_created: bool
    
    # Processing status
    cv_id: int | None
    error: str | None
    status: str  # "pending", "processing", "completed", "failed"
