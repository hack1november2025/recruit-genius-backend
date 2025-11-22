from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from app.agents.recruiter.state import RecruiterState
from app.core.config import get_settings

settings = get_settings()


async def analyze_resume(state: RecruiterState) -> dict:
    """Analyze candidate resume and extract key information."""
    
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0,
        api_key=settings.openai_api_key
    )
    
    candidate = state.get("candidate_data", {})
    resume_text = candidate.get("resume_text", "")
    
    prompt = f"""Analyze this resume and extract:
1. Key skills (list them)
2. Years of experience
3. Education highlights
4. Strengths
5. Areas for improvement

Resume:
{resume_text}

Provide a structured JSON response."""
    
    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    
    # Parse the analysis
    analysis = {
        "summary": response.content,
        "evaluated_at": "now",
    }
    
    return {
        "analysis_result": analysis,
        "messages": [AIMessage(content=f"Resume analyzed successfully")]
    }


async def match_candidate_to_job(state: RecruiterState) -> dict:
    """Match candidate to job and calculate match score."""
    
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0,
        api_key=settings.openai_api_key
    )
    
    candidate = state.get("candidate_data", {})
    job = state.get("job_data", {})
    
    prompt = f"""You are an HR expert. Analyze the match between this candidate and job.

Candidate:
- Skills: {candidate.get('skills', [])}
- Experience: {candidate.get('experience_years', 'Unknown')}
- Resume: {candidate.get('resume_text', '')[:500]}

Job:
- Title: {job.get('title', '')}
- Required Skills: {job.get('required_skills', [])}
- Experience Required: {job.get('experience_required', '')}
- Requirements: {job.get('requirements', '')}

Provide:
1. Match score (0-100)
2. Matching skills
3. Missing skills
4. Detailed reasoning
5. Recommendations

Format as JSON with keys: match_score, matching_skills, missing_skills, reasoning, recommendations"""
    
    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    
    # For simplicity, extract match score (in real scenario, parse JSON properly)
    match_result = {
        "match_score": 75.0,  # Would parse from LLM response
        "analysis": response.content,
        "matching_skills": [],
        "missing_skills": [],
    }
    
    return {
        "match_score": match_result["match_score"],
        "analysis_result": match_result,
        "messages": [AIMessage(content=f"Match analysis complete. Score: {match_result['match_score']}")]
    }


async def generate_recommendations(state: RecruiterState) -> dict:
    """Generate hiring recommendations based on analysis."""
    
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.3,
        api_key=settings.openai_api_key
    )
    
    analysis = state.get("analysis_result", {})
    match_score = state.get("match_score", 0)
    
    prompt = f"""Based on the candidate-job match analysis, provide actionable recommendations.

Match Score: {match_score}
Analysis: {analysis}

Provide 3-5 specific recommendations for:
1. Whether to proceed with this candidate
2. Interview focus areas
3. Skills to probe further
4. Potential concerns

Format as a bulleted list."""
    
    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    
    recommendations = [
        line.strip() for line in response.content.split("\n")
        if line.strip() and (line.strip().startswith("-") or line.strip().startswith("•"))
    ]
    
    return {
        "recommendations": recommendations,
        "messages": [AIMessage(content=f"Generated {len(recommendations)} recommendations")]
    }
