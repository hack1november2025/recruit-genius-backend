"""Semantic search repository for CV matching using LangChain vector store."""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.cv import CV
from app.db.models.candidate import Candidate
from app.services.vector_store_service import get_vector_store_service
from app.core.logging import rag_logger


class SemanticSearchRepository:
    """Repository for semantic search using LangChain vector store."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_store_service = get_vector_store_service()
    
    async def search_candidates(
        self,
        query_text: str,
        top_k: int = 50,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Perform RAG-only vector similarity search using LangChain vector store.
        
        This approach casts a wide net initially using semantic similarity only.
        Detailed metrics and filtering are calculated in a separate step.
        
        Args:
            query_text: Job description text to search for
            top_k: Maximum number of results to return (default 50 for wide net)
            similarity_threshold: Minimum cosine similarity score 0-1 (default 0.3 for very broad search)
            
        Returns:
            List of candidate records with similarity scores, CV text, and metadata
        """
        try:
            rag_logger.info(f"Starting RAG-only search with LangChain, top_k={top_k}, threshold={similarity_threshold}")
            
            # Perform semantic search using LangChain vector store
            results = await self.vector_store_service.similarity_search_with_score(
                query=query_text,
                k=top_k * 2,  # Get more results to account for grouping by CV
                filter_dict={"entity_type": "cv"}  # Only search CV documents
            )
            
            # Group results by cv_id and calculate average similarity
            cv_scores = {}
            for doc, score in results:
                # LangChain returns distance score, convert to similarity (1 - distance)
                similarity = 1 - score if score <= 1 else score
                
                # Skip if below threshold
                if similarity < similarity_threshold:
                    continue
                
                cv_id = doc.metadata.get("cv_id")
                if cv_id:
                    if cv_id not in cv_scores:
                        cv_scores[cv_id] = []
                    cv_scores[cv_id].append(similarity)
            
            # Calculate average similarity for each CV
            cv_avg_scores = {
                cv_id: sum(scores) / len(scores) 
                for cv_id, scores in cv_scores.items()
            }
            
            # Sort by average similarity and take top_k
            sorted_cvs = sorted(
                cv_avg_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:top_k]
            
            # Fetch CV and Candidate data
            candidates = []
            for cv_id, similarity_score in sorted_cvs:
                query = (
                    select(CV, Candidate)
                    .join(Candidate, CV.candidate_id == Candidate.id)
                    .where(CV.id == cv_id)
                    .where(CV.is_processed == True)
                )
                
                result = await self.db.execute(query)
                row = result.first()
                
                if row:
                    cv, candidate = row
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
