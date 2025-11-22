"""Node functions for the matcher agent workflow."""
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.agents.matcher.state import MatcherState
from app.db.models.job import Job
from app.db.models.job_metadata import JobMetadata
from app.repositories.hybrid_search import HybridSearchRepository
from app.repositories.cv_metrics import CVMetricsRepository
from app.services.cv_metrics_calculator import CVMetricsCalculator
from app.core.logging import rag_logger


async def retrieve_job_node(state: MatcherState, db: AsyncSession) -> Dict[str, Any]:
    """
    Retrieve job description, embedding, and metadata.
    
    Args:
        state: Current matcher state
        db: Database session
        
    Returns:
        Updated state with job information
    """
    job_id = state["job_id"]
    
    try:
        # Fetch job with metadata
        query = (
            select(Job)
            .options(joinedload(Job.job_metadata))
            .where(Job.id == job_id)
        )
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            return {
                "error": f"Job with id {job_id} not found"
            }
        
        # Check if job has embeddings in LangChain vector store
        from app.services.vector_store_service import get_vector_store_service
        vector_service = get_vector_store_service()
        
        try:
            # Search for any documents with this job_id
            # Try without filter first to see if any embeddings exist
            test_results = await vector_service.similarity_search(
                query=job.title or "test",
                k=1
            )
            
            rag_logger.info(f"Vector store check: found {len(test_results)} total documents")
            
            # Now try with filter
            filtered_results = await vector_service.similarity_search(
                query=job.title or "test",
                k=1,
                filter_dict={"job_id": job.id, "entity_type": "job"}
            )
            
            rag_logger.info(f"Filtered search for job {job.id}: found {len(filtered_results)} documents")
            
            if not filtered_results:
                return {
                    "error": f"Job {job_id} has not been processed. Please process the job first."
                }
        except Exception as e:
            rag_logger.warning(f"Could not verify job embeddings: {str(e)}")
            # Continue anyway - might be a temporary issue
        
        # Extract metadata
        job_metadata = {}
        if job.job_metadata:
            job_metadata = {
                "title": job.title,
                "department": job.department,
                "location": job.location,
                "required_skills": job.job_metadata.required_skills or [],
                "preferred_skills": job.job_metadata.preferred_skills or [],
                "min_experience_years": job.job_metadata.min_experience_years,
                "max_experience_years": job.job_metadata.max_experience_years,
                "seniority_level": job.job_metadata.seniority_level,
                "remote_type": job.job_metadata.remote_type,
                "locations": job.job_metadata.locations or [],
                "tech_stack": job.job_metadata.tech_stack or [],
                "full_metadata": job.job_metadata.full_metadata or {},
            }
        
        rag_logger.info(f"Retrieved job {job_id}: {job.title}")
        
        return {
            "job_data": {
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "department": job.department,
                "location": job.location,
            },
            "job_text": job.description,
            "job_metadata": job_metadata,
            "error": None,
        }
        
    except Exception as e:
        rag_logger.error(f"Error retrieving job {job_id}: {str(e)}")
        return {
            "error": f"Failed to retrieve job: {str(e)}"
        }





async def rag_search_node(state: MatcherState, db: AsyncSession) -> Dict[str, Any]:
    """
    Perform RAG-only vector similarity search using LangChain vector store.
    Casts a wide net to find semantically similar candidates.
    
    Args:
        state: Current matcher state
        db: Database session
        
    Returns:
        Updated state with candidate results
    """
    if state.get("error"):
        return {}
    
    job_text = state.get("job_text")
    top_k = state.get("top_k", 50)  # Wide net - get more candidates
    
    if not job_text:
        return {
            "error": "Job text not available"
        }
    
    try:
        repo = HybridSearchRepository(db)
        
        # Perform RAG-only search using LangChain vector store
        candidates = await repo.search_candidates(
            query_text=job_text,
            top_k=top_k,
            similarity_threshold=0.3  # Lower threshold to cast wider net
        )
        
        rag_logger.info(f"RAG search found {len(candidates)} candidates")
        
        return {
            "candidate_results": candidates,
            "error": None,
        }
        
    except Exception as e:
        rag_logger.error(f"RAG search failed: {str(e)}")
        return {
            "error": f"RAG search failed: {str(e)}"
        }


async def calculate_metrics_node(state: MatcherState, db: AsyncSession) -> Dict[str, Any]:
    """
    Calculate comprehensive metrics for each candidate CV against the job.
    Persists metrics to database for tracking and analysis.
    
    Args:
        state: Current matcher state with candidate_results
        db: Database session
        
    Returns:
        Updated state with metrics attached to candidates
    """
    if state.get("error"):
        return {}
    
    candidate_results = state.get("candidate_results", [])
    job_id = state["job_id"]
    job_metadata = state.get("job_metadata", {})
    job_text = state.get("job_text", "")
    
    if not candidate_results:
        rag_logger.info("No candidates to calculate metrics for")
        return {
            "candidate_results": [],
        }
    
    try:
        calculator = CVMetricsCalculator()
        metrics_repo = CVMetricsRepository(db)
        
        enhanced_candidates = []
        
        for result in candidate_results:
            cv_id = result["cv_id"]
            cv_metadata = result.get("cv_metadata", {})
            cv_text = result.get("cv_text", "")
            similarity_score = result["similarity_score"]
            
            rag_logger.info(f"Calculating metrics for CV {cv_id}")
            
            # Calculate all 8 metrics
            metrics = calculator.calculate_all_metrics(
                cv_metadata=cv_metadata,
                cv_text=cv_text,
                job_metadata=job_metadata,
                job_text=job_text,
                semantic_similarity=similarity_score
            )
            
            # Persist metrics to database
            await metrics_repo.upsert_metrics(
                cv_id=cv_id,
                job_id=job_id,
                metrics_data=metrics
            )
            
            # Add metrics to candidate result
            result["metrics"] = metrics
            enhanced_candidates.append(result)
        
        rag_logger.info(f"Calculated and persisted metrics for {len(enhanced_candidates)} candidates")
        
        return {
            "candidate_results": enhanced_candidates,
            "error": None,
        }
        
    except Exception as e:
        rag_logger.error(f"Metrics calculation failed: {str(e)}")
        return {
            "error": f"Metrics calculation failed: {str(e)}"
        }


def score_candidates_node(state: MatcherState) -> Dict[str, Any]:
    """
    Score and rank candidates based on comprehensive metrics.
    Uses the calculated metrics from calculate_metrics_node.
    
    Args:
        state: Current matcher state with metrics-enhanced candidates
        
    Returns:
        Updated state with scored, ranked candidates and summary
    """
    if state.get("error"):
        return {}
    
    job_metadata = state.get("job_metadata", {})
    candidate_results = state.get("candidate_results", [])
    
    if not candidate_results:
        return {
            "final_matches": [],
            "summary": {
                "role_title": job_metadata.get("title", "Unknown"),
                "primary_stack_or_domain": ", ".join(job_metadata.get("tech_stack", [])[:3]) or "General",
                "key_required_skills": job_metadata.get("required_skills", [])[:10],
                "nice_to_have_skills": job_metadata.get("preferred_skills", [])[:10],
                "hard_constraints_applied": ["RAG-only search (no hard filters)"]
            }
        }
    
    # Format candidates with metrics
    scored_candidates = []
    for result in candidate_results:
        candidate = result["candidate"]
        cv_metadata = result.get("cv_metadata", {})
        metrics = result.get("metrics", {})
        
        scored_candidates.append({
            "candidate_id": candidate.id,
            "cv_id": result["cv_id"],
            "name": cv_metadata.get("name") or candidate.name,
            "current_role": cv_metadata.get("current_role", "Not specified"),
            
            # Overall scores
            "match_score": metrics.get("composite_score", 0),
            "hybrid_similarity_score": result["similarity_score"],
            
            # Core Fit Metrics
            "skills_match_score": metrics.get("skills_match_score", 0),
            "experience_relevance_score": metrics.get("experience_relevance_score", 0),
            "education_fit_score": metrics.get("education_fit_score", 0),
            
            # Quality Metrics
            "achievement_impact_score": metrics.get("achievement_impact_score", 0),
            "keyword_density_score": metrics.get("keyword_density_score", 0),
            
            # Risk/Confidence Metrics
            "employment_gap_score": metrics.get("employment_gap_score", 0),
            "readability_score": metrics.get("readability_score", 0),
            "ai_confidence_score": metrics.get("ai_confidence_score", 0),
            
            # Additional context
            "experience": {
                "total_years_experience": cv_metadata.get("total_years_experience", 0),
                "relevant_experience_years": cv_metadata.get("total_years_experience", 0),
                "relevant_summary": cv_metadata.get("summary", "No summary available")[:200]
            },
            "seniority_match": cv_metadata.get("seniority_level", "Unknown"),
            "location_match": {
                "candidate_location": cv_metadata.get("country", ""),
                "candidate_city": cv_metadata.get("city", ""),
                "compatible": True  # RAG-only doesn't filter by location
            },
            
            # Rationale based on metrics
            "overall_rationale": _build_rationale_from_metrics(metrics, cv_metadata, job_metadata),
            "metrics_details": metrics.get("metric_details", {}),
        })
    
    # Sort by composite_score descending
    scored_candidates.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Take top matches for final output
    top_k = min(state.get("top_k", 10), 10)  # Cap at 10 for final results
    final_matches = scored_candidates[:top_k]
    
    rag_logger.info(f"Scored {len(scored_candidates)} candidates, returning top {len(final_matches)}")
    
    # Build summary
    summary = {
        "role_title": job_metadata.get("title", "Unknown"),
        "primary_stack_or_domain": ", ".join(job_metadata.get("tech_stack", [])[:3]) or "General",
        "key_required_skills": job_metadata.get("required_skills", [])[:10],
        "nice_to_have_skills": job_metadata.get("preferred_skills", [])[:10],
        "hard_constraints_applied": ["RAG-only search (no upfront filtering, all metrics calculated)"],
        "total_candidates_evaluated": len(candidate_results),
        "top_candidates_returned": len(final_matches),
    }
    
    return {
        "final_matches": final_matches,
        "summary": summary,
        "error": None,
    }


def _build_rationale_from_metrics(
    metrics: Dict[str, Any],
    cv_metadata: Dict[str, Any],
    job_metadata: Dict[str, Any]
) -> str:
    """Build human-readable rationale from calculated metrics."""
    parts = []
    
    composite = metrics.get("composite_score", 0)
    skills_match = metrics.get("skills_match_score", 0)
    experience = metrics.get("experience_relevance_score", 0)
    confidence = metrics.get("ai_confidence_score", 0)
    
    # Overall fit
    if composite >= 80:
        parts.append(f"Excellent overall match ({composite:.0f}%).")
    elif composite >= 60:
        parts.append(f"Good overall match ({composite:.0f}%).")
    else:
        parts.append(f"Moderate match ({composite:.0f}%).")
    
    # Skills
    if skills_match >= 80:
        parts.append(f"Strong skills alignment ({skills_match:.0f}%).")
    elif skills_match >= 60:
        parts.append(f"Reasonable skills match ({skills_match:.0f}%).")
    else:
        parts.append(f"Limited skills overlap ({skills_match:.0f}%).")
    
    # Experience
    years = cv_metadata.get("total_years_experience", 0)
    parts.append(f"{years} years experience (relevance score: {experience:.1f}/10).")
    
    # Confidence
    if confidence < 80:
        parts.append(f"Note: AI extraction confidence at {confidence:.0f}%.")
    
    return " ".join(parts)


def _calculate_match_score(
    job_metadata: Dict[str, Any],
    cv_metadata: Dict[str, Any],
    similarity_score: float
) -> Dict[str, Any]:
    """
    Calculate detailed match score breakdown.
    
    Returns a dictionary with:
    - match_score (0-100)
    - matched_skills, missing_required_skills, nice_to_have_covered
    - seniority_match, experience, location_match, language_match
    - other_factors, rationale
    """
    score = 0.0
    weights = {
        "semantic": 30,
        "required_skills": 40,
        "experience": 15,
        "seniority": 10,
        "nice_to_have": 5
    }
    
    # 1. Semantic similarity (30%)
    semantic_score = similarity_score * weights["semantic"]
    score += semantic_score
    
    # 2. Required skills match (40%)
    required_skills = {s.lower() for s in job_metadata.get("required_skills", [])}
    candidate_skills = {s.lower() for s in cv_metadata.get("skills", [])}
    
    matched_skills = list(required_skills & candidate_skills)
    missing_required_skills = list(required_skills - candidate_skills)
    
    if required_skills:
        skills_match_ratio = len(matched_skills) / len(required_skills)
        score += skills_match_ratio * weights["required_skills"]
    else:
        score += weights["required_skills"]  # No requirements, full points
    
    # 3. Experience match (15%)
    min_exp_required = job_metadata.get("min_experience_years", 0) or 0
    candidate_exp = cv_metadata.get("total_years_experience", 0) or 0
    
    if candidate_exp >= min_exp_required:
        exp_score = weights["experience"]
    elif candidate_exp >= min_exp_required * 0.8:  # 80% tolerance
        exp_score = weights["experience"] * 0.7
    else:
        exp_score = weights["experience"] * 0.3
    
    score += exp_score
    
    # 4. Seniority match (10%)
    job_seniority = (job_metadata.get("seniority_level") or "").lower()
    candidate_seniority = (cv_metadata.get("seniority_level") or "").lower()
    
    seniority_hierarchy = {"junior": 1, "mid": 2, "senior": 3, "lead": 4, "principal": 5}
    job_level = seniority_hierarchy.get(job_seniority, 2)
    candidate_level = seniority_hierarchy.get(candidate_seniority, 2)
    
    if candidate_level == job_level:
        seniority_match = "Exact"
        seniority_score = weights["seniority"]
    elif candidate_level > job_level:
        seniority_match = "Overqualified"
        seniority_score = weights["seniority"] * 0.8
    else:
        seniority_match = "Underqualified"
        seniority_score = weights["seniority"] * 0.4
    
    score += seniority_score
    
    # 5. Nice-to-have skills (5%)
    preferred_skills = {s.lower() for s in job_metadata.get("preferred_skills", [])}
    nice_to_have_covered = list(preferred_skills & candidate_skills)
    
    if preferred_skills:
        nice_ratio = len(nice_to_have_covered) / len(preferred_skills)
        score += nice_ratio * weights["nice_to_have"]
    else:
        score += weights["nice_to_have"]
    
    # Location match
    job_locations = job_metadata.get("locations", [])
    candidate_country = cv_metadata.get("country", "")
    candidate_city = cv_metadata.get("city", "")
    
    location_compatible = True
    if job_locations:
        location_compatible = any(
            loc.lower() in candidate_country.lower() or 
            loc.lower() in candidate_city.lower()
            for loc in job_locations
        )
    
    job_remote = job_metadata.get("remote_type", "remote").lower()
    candidate_remote = cv_metadata.get("location_type_preference", "remote").lower()
    
    location_match = {
        "job_location_type": job_remote.capitalize(),
        "candidate_location_type_preference": candidate_remote.capitalize(),
        "compatible": location_compatible,
        "notes": f"Candidate prefers {candidate_remote}, job is {job_remote}"
    }
    
    # Language match
    job_languages = job_metadata.get("full_metadata", {}).get("languages_required", [])
    candidate_languages = cv_metadata.get("languages", [])
    
    language_compatible = True
    if job_languages:
        # Simple check - at least one language matches
        language_compatible = any(
            any(jlang.lower() in clang.lower() for clang in candidate_languages)
            for jlang in job_languages
        )
    
    language_match = {
        "job_languages_required": job_languages,
        "candidate_languages": candidate_languages,
        "compatible": language_compatible
    }
    
    # Other factors
    other_factors = []
    if cv_metadata.get("availability"):
        other_factors.append(f"Available: {cv_metadata['availability']}")
    if cv_metadata.get("current_company"):
        other_factors.append(f"Currently at {cv_metadata['current_company']}")
    
    # Build rationale
    rationale_parts = []
    rationale_parts.append(f"Semantic similarity: {similarity_score:.2f}.")
    
    if matched_skills:
        rationale_parts.append(f"Matches {len(matched_skills)}/{len(required_skills)} required skills.")
    
    if missing_required_skills:
        rationale_parts.append(f"Missing: {', '.join(missing_required_skills[:3])}.")
    
    rationale_parts.append(f"{seniority_match} for seniority level.")
    rationale_parts.append(f"{candidate_exp} years experience (requires {min_exp_required}+).")
    
    rationale = " ".join(rationale_parts)
    
    return {
        "match_score": round(min(score, 100), 2),
        "matched_skills": matched_skills,
        "missing_required_skills": missing_required_skills,
        "nice_to_have_covered": nice_to_have_covered,
        "seniority_match": seniority_match,
        "experience": {
            "total_years_experience": candidate_exp,
            "relevant_experience_years": candidate_exp,  # Could be refined
            "relevant_summary": cv_metadata.get("summary", "No summary available")[:200]
        },
        "location_match": location_match,
        "language_match": language_match,
        "other_factors": other_factors,
        "rationale": rationale
    }


def _format_constraints(filters: Dict[str, Any]) -> List[str]:
    """Format metadata filters into human-readable constraints."""
    constraints = []
    
    if "required_skills" in filters:
        skills = filters["required_skills"][:3]
        constraints.append(f"Skills: {', '.join(skills)}")
    
    if "min_experience_years" in filters:
        constraints.append(f"Min experience: {filters['min_experience_years']}+ years")
    
    if "seniority_level" in filters:
        levels = filters["seniority_level"]
        if isinstance(levels, list):
            constraints.append(f"Seniority: {', '.join(levels).title()}")
        else:
            constraints.append(f"Seniority: {levels.title()}")
    
    if "languages" in filters:
        constraints.append(f"Languages: {', '.join(filters['languages'])}")
    
    if "remote_type" in filters:
        rt = filters["remote_type"]
        if isinstance(rt, list):
            constraints.append(f"Location type: {' or '.join(rt).title()}")
        else:
            constraints.append(f"Location type: {rt.title()}")
    
    if "locations" in filters:
        constraints.append(f"Locations: {', '.join(filters['locations'])}")
    
    return constraints or ["No hard constraints applied"]
