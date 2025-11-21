"""CV Embeddings model for vector search."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.db.base import Base


class CVEmbedding(Base):
    """CV text chunks with vector embeddings for semantic search."""
    
    __tablename__ = "cv_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)  # OpenAI text-embedding-3-small dimension
    embedding_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        {"schema": None}  # Use default schema
    )
