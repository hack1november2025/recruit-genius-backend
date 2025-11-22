"""Job metadata extraction service using LLM."""
import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.core.config import get_settings
from app.core.logging import llm_logger


class JobMetadataStructure(BaseModel):
    """Structured job metadata."""
    
    # Core Requirements
    required_skills: list[str] = Field(description="Required technical skills")
    preferred_skills: list[str] = Field(description="Preferred/nice-to-have skills")
    min_experience_years: int | None = Field(description="Minimum years of experience required")
    max_experience_years: int | None = Field(description="Maximum years of experience")
    
    # Education
    required_education: str | None = Field(description="Required education level")
    preferred_education: str | None = Field(description="Preferred education level")
    
    # Location & Remote
    remote_type: str | None = Field(description="Remote work type: 'remote', 'hybrid', 'onsite'")
    locations: list[str] = Field(description="Acceptable work locations")
    
    # Seniority & Role
    seniority_level: str | None = Field(description="Seniority level: 'junior', 'mid', 'senior', 'lead', 'principal'")
    role_type: str | None = Field(description="Role type: 'individual_contributor', 'manager', 'director'")
    
    # Compensation
    min_salary: float | None = Field(description="Minimum salary")
    max_salary: float | None = Field(description="Maximum salary")
    currency: str = Field(description="Currency code (e.g., USD, EUR)", default="USD")
    
    # Certifications
    required_certifications: list[str] = Field(description="Required certifications")
    preferred_certifications: list[str] = Field(description="Preferred certifications")
    
    # Additional
    responsibilities: list[str] = Field(description="Key responsibilities")
    benefits: list[str] = Field(description="Benefits and perks")
    tech_stack: list[str] = Field(description="Technologies and tools used")


class JobMetadataExtractionService:
    """Service for extracting structured metadata from job descriptions using LLM."""
    
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        self.parser = JsonOutputParser(pydantic_object=JobMetadataStructure)
    
    async def extract_job_metadata(self, job_description: str) -> Dict:
        """
        Extract structured metadata from job description.
        
        Args:
            job_description: Full job description text
            
        Returns:
            Dictionary with extracted job metadata
        """
        llm_logger.info("Extracting metadata from job description")
        
        system_prompt = f"""You are an expert HR analyst. Extract structured information from the job description.

Be thorough and accurate. If information is not available, use null or empty array.

For experience, extract min/max years if mentioned (e.g., "3-5 years" -> min: 3, max: 5).

For remote type, determine if it's "remote", "hybrid", or "onsite".

For seniority, infer from title and requirements: "junior", "mid", "senior", "lead", "principal".

{self.parser.get_format_instructions()}"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Extract all relevant information from this job description:\n\n{job_description}")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            try:
                metadata = json.loads(response.content)
                llm_logger.info("Successfully extracted job metadata")
                return metadata
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code block
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                metadata = json.loads(content)
                llm_logger.info("Successfully extracted job metadata (after markdown cleanup)")
                return metadata
                
        except Exception as e:
            llm_logger.error(f"Job metadata extraction failed: {str(e)}")
            raise
