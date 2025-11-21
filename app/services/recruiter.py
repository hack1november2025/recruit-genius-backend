from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.candidate import CandidateRepository
from app.repositories.job import JobRepository
from app.repositories.match import MatchRepository
from app.agents.recruiter.graph import create_recruiter_graph
from langchain_core.messages import HumanMessage
import uuid


class RecruiterService:
    """Service for recruitment operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.candidate_repo = CandidateRepository(db)
        self.job_repo = JobRepository(db)
        self.match_repo = MatchRepository(db)
    
    async def analyze_candidate_resume(self, candidate_id: int) -> dict:
        """Analyze candidate resume using AI agent."""
        
        candidate = await self.candidate_repo.get(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        # Create agent graph
        graph = create_recruiter_graph()
        
        # Prepare initial state
        initial_state = {
            "messages": [HumanMessage(content="Analyze this candidate's resume")],
            "candidate_data": {
                "name": candidate.name,
                "email": candidate.email,
                "resume_text": candidate.resume_text or "",
                "skills": candidate.skills,
                "experience_years": candidate.experience_years,
                "education": candidate.education,
            },
            "job_data": None,
            "analysis_result": None,
            "match_score": None,
            "recommendations": [],
        }
        
        # Execute only the analyze node
        result = await graph.ainvoke(initial_state)
        
        analysis = result.get("analysis_result", {})
        
        # Update candidate with analysis
        await self.candidate_repo.update(candidate_id, analysis=analysis)
        
        return analysis
    
    async def match_candidate_to_job(self, candidate_id: int, job_id: int) -> dict:
        """Match a candidate to a job using AI agent."""
        
        candidate = await self.candidate_repo.get(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        job = await self.job_repo.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Create agent graph
        graph = create_recruiter_graph()
        
        # Prepare initial state
        initial_state = {
            "messages": [HumanMessage(content="Match this candidate to the job")],
            "candidate_data": {
                "name": candidate.name,
                "email": candidate.email,
                "resume_text": candidate.resume_text or "",
                "skills": candidate.skills,
                "experience_years": candidate.experience_years,
                "education": candidate.education,
            },
            "job_data": {
                "title": job.title,
                "department": job.department,
                "description": job.description,
                "requirements": job.requirements,
                "required_skills": job.required_skills,
                "experience_required": job.experience_required,
            },
            "analysis_result": None,
            "match_score": None,
            "recommendations": [],
        }
        
        # Execute the full graph
        result = await graph.ainvoke(initial_state)
        
        match_score = result.get("match_score", 0)
        analysis = result.get("analysis_result", {})
        recommendations = result.get("recommendations", [])
        
        # Create match record
        match = await self.match_repo.create(
            candidate_id=candidate_id,
            job_id=job_id,
            match_score=match_score,
            reasoning=analysis.get("analysis", ""),
            matching_skills=analysis.get("matching_skills", []),
            missing_skills=analysis.get("missing_skills", []),
            ai_insights={
                "recommendations": recommendations,
                "full_analysis": analysis,
            },
        )
        
        return {
            "match_id": match.id,
            "match_score": match_score,
            "reasoning": match.reasoning,
            "matching_skills": match.matching_skills,
            "missing_skills": match.missing_skills,
            "recommendations": recommendations,
        }
