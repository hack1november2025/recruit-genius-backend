"""RAG-only search repository for CV matching using pure vector similarity."""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
from app.db.models.cv import CV
from app.db.models.cv_embedding import CVEmbedding
from app.db.models.candidate import Candidate
from app.core.logging import rag_logger


class HybridSearchRepository:
    """Repository for RAG-only search using pure vector similarity."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def search_candidates(
        self,
        query_embedding: List[float],
        top_k: int = 50,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Perform RAG-only vector similarity search without metadata filters.
        
        This approach casts a wide net initially using semantic similarity only.
        Detailed metrics and filtering are calculated in a separate step.
        
        Args:
            query_embedding: Vector embedding of the job description
            top_k: Maximum number of results to return (default 50 for wide net)
            similarity_threshold: Minimum cosine similarity score 0-1 (default 0.3 for very broad search)
            
        Returns:
            List of candidate records with similarity scores, CV text, and metadata
        """
        try:
            rag_logger.info(f"Starting RAG-only search, top_k={top_k}, threshold={similarity_threshold}")
            
            # Perform pure vector similarity search
            # Using pgvector's <=> operator for cosine distance
            # Note: cosine distance = 1 - cosine similarity
            query = (
                select(
                    CVEmbedding.cv_id,
                    func.avg(1 - CVEmbedding.embedding.cosine_distance(query_embedding)).label("similarity_score"),
                    CV,
                    Candidate
                )
                .join(CV, CVEmbedding.cv_id == CV.id)
                .join(Candidate, CV.candidate_id == Candidate.id)
                .where(CV.is_processed == True)
                .group_by(CVEmbedding.cv_id, CV.id, Candidate.id)
                .having(func.avg(1 - CVEmbedding.embedding.cosine_distance(query_embedding)) >= similarity_threshold)
                .order_by(text("similarity_score DESC"))
                .limit(top_k)
            )
            
            result = await self.db.execute(query)
            rows = result.all()
            
            # Format results with full CV text for metrics calculation
            candidates = []
            for row in rows:
                cv_id, similarity_score, cv, candidate = row
                candidates.append({
                    "candidate_id": candidate.id,
                    "cv_id": cv_id,
                    "similarity_score": float(similarity_score),
                    "candidate": candidate,
                    "cv": cv,
                    "cv_text": cv.original_text or "",  # Full CV text for metrics
                    "cv_metadata": cv.structured_metadata or {},
                })
            
            rag_logger.info(f"RAG search returned {len(candidates)} candidates")
            return candidates
            
        except Exception as e:
            rag_logger.error(f"RAG search failed: {str(e)}")
            raise
