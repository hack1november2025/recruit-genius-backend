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
        Find best matching candidates for a job using hybrid search.
        
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
            candidates: List of matched candidates with scores
        """
        try:
            for candidate in candidates:
                await self.match_repo.create(
                    job_id=job_id,
                    candidate_id=candidate["candidate_id"],
                    match_score=candidate["match_score"],
                    reasoning=candidate["overall_rationale"],
                    matching_skills=candidate["matched_skills"],
                    missing_skills=candidate["missing_required_skills"],
                    ai_insights={
                        "seniority_match": candidate["seniority_match"],
                        "experience": candidate["experience"],
                        "location_match": candidate["location_match"],
                        "language_match": candidate["language_match"],
                        "other_factors": candidate["other_relevant_factors"],
                        "similarity_score": candidate["hybrid_similarity_score"],
                    }
                )
            
            rag_logger.info(f"Persisted {len(candidates)} matches for job {job_id}")
            
        except Exception as e:
            rag_logger.error(f"Failed to persist matches: {str(e)}")
            # Don't raise - this is non-critical
