"""Service for AI-powered job description generation."""
import time
from app.agents.job_generator.graph import create_job_generator_graph
from app.agents.job_generator.state import JobGeneratorState
from app.schemas.job_description import JobDescriptionGenerateRequest, JobDescriptionResponse
from app.core.logging import llm_logger


class JobGeneratorService:
    """Service to orchestrate job description generation."""
    
    def __init__(self):
        self.graph = create_job_generator_graph()
    
    async def generate_description(
        self, 
        request: JobDescriptionGenerateRequest
    ) -> JobDescriptionResponse:
        """
        Generate a complete job description from a brief.
        
        Args:
            request: Generation request with brief and parameters
            
        Returns:
            Complete job description with metadata
        """
        start_time = time.time()
        
        # Prepare initial state
        initial_state: JobGeneratorState = {
            "messages": [],
            "brief_description": request.brief_description,
            "department": request.department,
            "location": request.location,
            "employment_type": request.employment_type,
            "salary_range": request.salary_range,
            "tone": request.tone,
            "job_title": None,
            "full_description": None,
            "responsibilities": [],
            "required_qualifications": [],
            "preferred_qualifications": [],
            "benefits": [],
            "inclusivity_score": 100.0,
            "flagged_terms": [],
            "needs_regeneration": False,
        }
        
        # Execute graph
        llm_logger.info(f"Generating job description for: {request.brief_description[:50]}...")
        
        result = await self.graph.ainvoke(initial_state)
        
        generation_time = int((time.time() - start_time) * 1000)
        
        llm_logger.info(f"Job description generated in {generation_time}ms")
        
        # Build response
        response = JobDescriptionResponse(
            job_title=result["job_title"] or "Untitled Position",
            full_description=result["full_description"] or "",
            responsibilities=result["responsibilities"],
            required_qualifications=result["required_qualifications"],
            preferred_qualifications=result["preferred_qualifications"],
            benefits=result["benefits"],
            inclusivity_score=result["inclusivity_score"],
            flagged_terms=result["flagged_terms"],
            generation_time_ms=generation_time,
            department=request.department,
            location=request.location,
            employment_type=request.employment_type,
            salary_range=request.salary_range,
        )
        
        return response
    
    async def generate_description_stream(
        self,
        request: JobDescriptionGenerateRequest
    ):
        """
        Generate job description with streaming updates.
        
        Args:
            request: Generation request
            
        Yields:
            Partial state updates as they complete
        """
        # Prepare initial state
        initial_state: JobGeneratorState = {
            "messages": [],
            "brief_description": request.brief_description,
            "department": request.department,
            "location": request.location,
            "employment_type": request.employment_type,
            "salary_range": request.salary_range,
            "tone": request.tone,
            "job_title": None,
            "full_description": None,
            "responsibilities": [],
            "required_qualifications": [],
            "preferred_qualifications": [],
            "benefits": [],
            "inclusivity_score": 100.0,
            "flagged_terms": [],
            "needs_regeneration": False,
        }
        
        llm_logger.info(f"Streaming job description generation for: {request.brief_description[:50]}...")
        
        # Stream updates from graph
        async for event in self.graph.astream(initial_state):
            # Each event is a dict with node name as key
            for node_name, node_output in event.items():
                yield {
                    "node": node_name,
                    "data": node_output
                }
