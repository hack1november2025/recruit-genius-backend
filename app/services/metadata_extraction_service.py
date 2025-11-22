"""Metadata extraction service for CVs using LLM."""
import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.core.config import get_settings
from app.core.logging import llm_logger


class WorkExperience(BaseModel):
    """Work experience entry."""
    company: str = Field(description="Company name")
    position: str = Field(description="Job title/position")
    start_date: str | None = Field(description="Start date (YYYY-MM format if available)")
    end_date: str | None = Field(description="End date (YYYY-MM format or 'Present')")
    duration_months: int | None = Field(description="Duration in months")
    responsibilities: list[str] = Field(description="Key responsibilities and achievements")
    technologies: list[str] = Field(description="Technologies/tools used")


class Education(BaseModel):
    """Education entry."""
    institution: str = Field(description="University/institution name")
    degree: str = Field(description="Degree type (Bachelor's, Master's, PhD, etc.)")
    field_of_study: str = Field(description="Major/field of study")
    graduation_year: int | None = Field(description="Graduation year")
    gpa: str | None = Field(description="GPA if mentioned")


class Certification(BaseModel):
    """Certification entry."""
    name: str = Field(description="Certification name")
    issuing_organization: str = Field(description="Issuing organization")
    issue_date: str | None = Field(description="Issue date")
    expiry_date: str | None = Field(description="Expiry date if applicable")


class CVMetadataStructure(BaseModel):
    """Structured CV metadata."""
    
    # Personal Info
    full_name: str | None = Field(description="Full name of candidate")
    email: str | None = Field(description="Email address")
    phone: str | None = Field(description="Phone number")
    location: str | None = Field(description="Current location/city")
    linkedin_url: str | None = Field(description="LinkedIn profile URL")
    github_url: str | None = Field(description="GitHub profile URL")
    portfolio_url: str | None = Field(description="Portfolio website URL")
    
    # Professional Summary
    professional_summary: str | None = Field(description="Professional summary or objective")
    years_of_experience: int | None = Field(description="Total years of professional experience")
    
    # Skills
    technical_skills: list[str] = Field(description="Technical skills (programming languages, frameworks, tools)")
    soft_skills: list[str] = Field(description="Soft skills (communication, leadership, etc.)")
    languages: list[dict] = Field(description="Spoken languages with proficiency level")
    
    # Experience
    work_experience: list[WorkExperience] = Field(description="Work experience history")
    total_experience_months: int | None = Field(description="Total months of work experience")
    
    # Education
    education: list[Education] = Field(description="Education history")
    highest_education_level: str | None = Field(description="Highest education level achieved")
    
    # Certifications
    certifications: list[Certification] = Field(description="Professional certifications")
    
    # Additional
    projects: list[dict] = Field(description="Notable projects")
    publications: list[str] = Field(description="Publications or papers")
    awards: list[str] = Field(description="Awards and recognitions")
    
    # Quality Indicators
    has_employment_gaps: bool = Field(description="Whether there are significant employment gaps")
    employment_gap_details: str | None = Field(description="Details about employment gaps if present")
    career_progression: str = Field(description="Assessment of career progression (e.g., 'upward', 'lateral', 'mixed')")


class MetadataExtractionService:
    """Service for extracting structured metadata from CV text using LLM."""
    
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0.0,
            openai_api_key=settings.openai_api_key
        )
        self.parser = JsonOutputParser(pydantic_object=CVMetadataStructure)
    
    async def extract_metadata(self, cv_text: str) -> Dict:
        """
        Extract structured metadata from CV text.
        
        Args:
            cv_text: CV text (preferably in English)
            
        Returns:
            Dictionary with extracted metadata
        """
        llm_logger.info("Extracting metadata from CV")
        
        system_prompt = f"""You are an expert CV/résumé parser. Extract structured information from the CV text.

Be thorough and accurate. If information is not available, use null.

For dates, use YYYY-MM format when possible. For current positions, use "Present".

For employment gaps, analyze the timeline and identify gaps > 3 months.

For career progression, assess whether the candidate has moved to more senior roles, similar roles, or varied roles.

{self.parser.get_format_instructions()}"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Extract all relevant information from this CV:\n\n{cv_text}")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            try:
                metadata = json.loads(response.content)
                llm_logger.info("Successfully extracted CV metadata")
                return metadata
            except json.JSONDecodeError as e:
                llm_logger.error(f"Failed to parse JSON response: {e}")
                # Try to extract JSON from markdown code block
                content = response.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                metadata = json.loads(content)
                llm_logger.info("Successfully extracted CV metadata (after markdown cleanup)")
                return metadata
                
        except Exception as e:
            llm_logger.error(f"Metadata extraction failed: {str(e)}")
            raise
    
    def calculate_quality_scores(self, metadata: Dict) -> Dict[str, float]:
        """
        Calculate quality/risk scores based on extracted metadata.
        
        Args:
            metadata: Extracted metadata dictionary
            
        Returns:
            Dictionary with calculated scores
        """
        scores = {
            "employment_gap_score": 10.0,  # Default: no gaps
            "readability_score": 8.0,  # Default: good
            "ai_confidence_score": 90.0,  # Default: high confidence
        }
        
        # Employment gap scoring (10 = no gaps, 0 = significant gaps)
        if metadata.get("has_employment_gaps"):
            scores["employment_gap_score"] = 5.0  # Moderate penalty
            if metadata.get("employment_gap_details") and "year" in metadata.get("employment_gap_details", "").lower():
                scores["employment_gap_score"] = 2.0  # Higher penalty for long gaps
        
        # Readability score based on data completeness
        completeness_fields = [
            "full_name", "email", "professional_summary",
            "technical_skills", "work_experience", "education"
        ]
        filled_fields = sum(1 for field in completeness_fields if metadata.get(field))
        scores["readability_score"] = (filled_fields / len(completeness_fields)) * 10
        
        # AI confidence based on data richness
        work_exp = metadata.get("work_experience", [])
        education = metadata.get("education", [])
        skills = metadata.get("technical_skills", [])
        
        confidence = 50.0  # Base confidence
        if work_exp:
            confidence += 20.0
        if education:
            confidence += 15.0
        if skills:
            confidence += 15.0
        
        scores["ai_confidence_score"] = min(confidence, 100.0)
        
        return scores
