"""CV model for storing multiple CVs per candidate."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class CV(Base):
    """CV model - allows multiple CVs per candidate."""
    
    __tablename__ = "cvs"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Original CV data
    original_text = Column(Text, nullable=False)  # Original text in any language
    translated_text = Column(Text, nullable=True)  # Translated to English
    original_language = Column(String(10), nullable=True)  # e.g., "es", "fr", "en"
    
    # File metadata
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Extracted basic info
    extracted_name = Column(String(255), nullable=True)
    extracted_email = Column(String(255), nullable=True)
    extracted_phone = Column(String(50), nullable=True)
    
    # Structured metadata (extracted by LLM)
    structured_metadata = Column(JSON, nullable=True)  # Skills, experience, education, etc.
    
    # Processing flags
    is_processed = Column(Boolean, default=False, nullable=False)
    is_translated = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
