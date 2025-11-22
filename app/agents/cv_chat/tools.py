"""Tools for CV Chat agent - RAG retrieval and candidate operations."""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from app.db.models.candidate import Candidate
from app.db.models.cv import CV
from app.db.models.cv_embedding import CVEmbedding
from app.repositories.hybrid_search import HybridSearchRepository
from app.services.embedding_service import EmbeddingService
from app.core.logging import rag_logger


async def search_candidates_by_query(
    db: AsyncSession,
    query_text: str,
    top_k: int = 10,
    similarity_threshold: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Search candidates using natural language query via RAG.
    
    Args:
        db: Database session
        query_text: Natural language search query
        top_k: Maximum number of results
        similarity_threshold: Minimum similarity score (0-1)
        
    Returns:
        List of candidate dictionaries with similarity scores
    """
    try:
        # Generate embedding for the query
        embedding_service = EmbeddingService()
        query_embedding = await embedding_service.generate_embedding(query_text)
        
        # Use hybrid search repository for RAG search
        search_repo = HybridSearchRepository(db)
        results = await search_repo.search_candidates(
            query_embedding=query_embedding,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        # Format results for chat agent
        formatted_results = []
        for result in results:
            candidate = result["candidate"]
            cv = result["cv"]
            cv_metadata = cv.structured_metadata or {}
            
            formatted_results.append({
                "candidate_id": candidate.id,
                "candidate_name": candidate.name,
                "candidate_email": candidate.email,
                "cv_id": result["cv_id"],
                "similarity_score": result["similarity_score"],
                "skills": cv_metadata.get("skills", []),
                "experience_years": cv_metadata.get("experience_years"),
                "education": cv_metadata.get("education", []),
                "job_titles": cv_metadata.get("job_titles", []),
                "companies": cv_metadata.get("companies", []),
                "location": cv_metadata.get("location"),
                "summary": cv_metadata.get("summary", ""),
                "cv_text_preview": result["cv_text"][:500] if result["cv_text"] else ""
            })
        
        rag_logger.info(f"Found {len(formatted_results)} candidates for query: {query_text[:100]}")
        return formatted_results
        
    except Exception as e:
        rag_logger.error(f"Error searching candidates by query: {str(e)}")
        raise


async def get_candidate_details(
    db: AsyncSession,
    candidate_id: int
) -> Dict[str, Any] | None:
    """
    Get detailed information about a specific candidate.
    
    Args:
        db: Database session
        candidate_id: ID of the candidate
        
    Returns:
        Detailed candidate information or None if not found
    """
    try:
        query = (
            select(Candidate, CV)
            .join(CV, Candidate.id == CV.candidate_id)
            .where(Candidate.id == candidate_id)
        )
        
        result = await db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        candidate, cv = row
        cv_metadata = cv.structured_metadata or {}
        
        return {
            "candidate_id": candidate.id,
            "candidate_name": candidate.name,
            "candidate_email": candidate.email,
            "candidate_phone": candidate.phone,
            "candidate_status": candidate.status.value if candidate.status else None,
            "cv_id": cv.id,
            "skills": cv_metadata.get("skills", []),
            "experience_years": cv_metadata.get("experience_years"),
            "education": cv_metadata.get("education", []),
            "job_titles": cv_metadata.get("job_titles", []),
            "companies": cv_metadata.get("companies", []),
            "location": cv_metadata.get("location"),
            "summary": cv_metadata.get("summary", ""),
            "languages": cv_metadata.get("languages", []),
            "certifications": cv_metadata.get("certifications", []),
            "cv_full_text": cv.original_text,
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
        }
        
    except Exception as e:
        rag_logger.error(f"Error getting candidate details for ID {candidate_id}: {str(e)}")
        raise


async def compare_candidates(
    db: AsyncSession,
    candidate_ids: List[int]
) -> List[Dict[str, Any]]:
    """
    Retrieve multiple candidates for comparison.
    
    Args:
        db: Database session
        candidate_ids: List of candidate IDs to compare
        
    Returns:
        List of candidate details for comparison
    """
    try:
        candidates = []
        for candidate_id in candidate_ids:
            details = await get_candidate_details(db, candidate_id)
            if details:
                candidates.append(details)
        
        rag_logger.info(f"Retrieved {len(candidates)} candidates for comparison")
        return candidates
        
    except Exception as e:
        rag_logger.error(f"Error comparing candidates: {str(e)}")
        raise


async def filter_candidates_by_criteria(
    db: AsyncSession,
    base_candidate_ids: List[int],
    criteria: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Filter a list of candidates by specific criteria.
    
    Args:
        db: Database session
        base_candidate_ids: Starting set of candidate IDs
        criteria: Dictionary of filter criteria (skills, experience_years, location, etc.)
        
    Returns:
        Filtered list of candidates
    """
    try:
        # Build dynamic filters based on criteria
        query = (
            select(Candidate, CV)
            .join(CV, Candidate.id == CV.candidate_id)
            .where(Candidate.id.in_(base_candidate_ids))
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        # Apply metadata-based filtering
        filtered_results = []
        for candidate, cv in rows:
            cv_metadata = cv.structured_metadata or {}
            
            # Check each criterion
            matches = True
            
            # Skills filter (case-insensitive, partial match)
            if "skills" in criteria and criteria["skills"]:
                required_skills = [s.lower() for s in criteria["skills"]]
                candidate_skills = [s.lower() for s in cv_metadata.get("skills", [])]
                if not any(skill in candidate_skills for skill in required_skills):
                    matches = False
            
            # Experience years filter (minimum)
            if "min_experience_years" in criteria:
                exp_years = cv_metadata.get("experience_years")
                if exp_years is None or exp_years < criteria["min_experience_years"]:
                    matches = False
            
            # Location filter (case-insensitive, partial match)
            if "location" in criteria and criteria["location"]:
                candidate_location = (cv_metadata.get("location") or "").lower()
                required_location = criteria["location"].lower()
                if required_location not in candidate_location:
                    matches = False
            
            # Companies filter (worked at any of these companies)
            if "companies" in criteria and criteria["companies"]:
                required_companies = [c.lower() for c in criteria["companies"]]
                candidate_companies = [c.lower() for c in cv_metadata.get("companies", [])]
                if not any(company in candidate_companies for company in required_companies):
                    matches = False
            
            if matches:
                filtered_results.append({
                    "candidate_id": candidate.id,
                    "candidate_name": candidate.name,
                    "candidate_email": candidate.email,
                    "cv_id": cv.id,
                    "skills": cv_metadata.get("skills", []),
                    "experience_years": cv_metadata.get("experience_years"),
                    "location": cv_metadata.get("location"),
                    "companies": cv_metadata.get("companies", []),
                    "job_titles": cv_metadata.get("job_titles", []),
                })
        
        rag_logger.info(f"Filtered {len(filtered_results)} candidates from {len(base_candidate_ids)} based on criteria")
        return filtered_results
        
    except Exception as e:
        rag_logger.error(f"Error filtering candidates: {str(e)}")
        raise
