"""Matcher service for orchestrating candidate-job matching."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.matcher.graph import run_matcher_workflow
from app.repositories.match import MatchRepository
from app.core.logging import rag_logger


class MatcherService:
    """Service to orchestrate job-candidate matching using the matcher agent."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.match_repo = MatchRepository(db)
    
    async def find_matches_for_job(
        self,
        job_id: int,
        top_k: int = 10,
        hard_constraints_overrides: dict | None = None,
        persist_matches: bool = True
    ) -> dict:
        """
        Find best matching candidates for a job using semantic search.
        
        Args:
            job_id: Job ID to match candidates against
            top_k: Maximum number of candidates to return
            hard_constraints_overrides: Optional filters to override job metadata
            persist_matches: Whether to save matches to database
            
        Returns:
            Dictionary with match results in the specified format
        """
        rag_logger.info(f"Finding matches for job_id={job_id}, top_k={top_k}")
        
        # Run matcher workflow
        result = await run_matcher_workflow(
            job_id=job_id,
            db=self.db,
            top_k=top_k,
            hard_constraints_overrides=hard_constraints_overrides
        )
        
        # If successful and persist_matches is True, save to database
        if persist_matches and not result.get("error") and result.get("candidates"):
            await self._persist_matches(job_id, result["candidates"])
        
        return result
    
    async def _persist_matches(self, job_id: int, candidates: list[dict]) -> None:
        """
        Persist match results to the matches table.
        
        Args:
            job_id: Job ID
            candidates: List of matched candidates with comprehensive metrics
        """
        try:
            for candidate in candidates:
                await self.match_repo.create(
                    job_id=job_id,
                    candidate_id=candidate["candidate_id"],
                    match_score=candidate["match_score"],
                    reasoning=candidate["overall_rationale"],
                    matching_skills=[],  # Not extracted in new format
                    missing_skills=[],  # Not extracted in new format
                    ai_insights={
                        # Core metrics
                        "skills_match_score": candidate.get("skills_match_score", 0),
                        "experience_relevance_score": candidate.get("experience_relevance_score", 0),
                        "education_fit_score": candidate.get("education_fit_score", 0),
                        
                        # Quality metrics
                        "achievement_impact_score": candidate.get("achievement_impact_score", 0),
                        "keyword_density_score": candidate.get("keyword_density_score", 0),
                        
                        # Risk/confidence metrics
                        "employment_gap_score": candidate.get("employment_gap_score", 0),
                        "readability_score": candidate.get("readability_score", 0),
                        "ai_confidence_score": candidate.get("ai_confidence_score", 0),
                        
                        # Additional context
                        "seniority_match": candidate.get("seniority_match", "Unknown"),
                        "experience": candidate.get("experience", {}),
                        "location_match": candidate.get("location_match", {}),
                        "similarity_score": candidate.get("semantic_similarity_score", 0),
                        "metrics_details": candidate.get("metrics_details", {}),
                    }
                )
            
            rag_logger.info(f"Persisted {len(candidates)} matches for job {job_id}")
            
        except Exception as e:
            rag_logger.error(f"Failed to persist matches: {str(e)}")
            # Don't raise - this is non-critical
