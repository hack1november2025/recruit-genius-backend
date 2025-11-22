"""Node functions for the matcher agent workflow."""
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.agents.matcher.state import MatcherState
from app.db.models.job import Job
from app.db.models.job_embedding import JobEmbedding
from app.db.models.job_metadata import JobMetadata
from app.repositories.hybrid_search import HybridSearchRepository
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
        
        # Fetch job embeddings (average of all chunks)
        embedding_query = select(JobEmbedding).where(JobEmbedding.job_id == job_id)
        embedding_result = await db.execute(embedding_query)
        embeddings = embedding_result.scalars().all()
        
        if not embeddings:
            return {
                "error": f"No embeddings found for job {job_id}. Please process the job first."
            }
        
        # Average embeddings across chunks
        avg_embedding = _average_embeddings([e.embedding for e in embeddings])
        
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
            "job_embedding": avg_embedding,
            "job_metadata": job_metadata,
            "error": None,
        }
        
    except Exception as e:
        rag_logger.error(f"Error retrieving job {job_id}: {str(e)}")
        return {
            "error": f"Failed to retrieve job: {str(e)}"
        }


def build_filters_node(state: MatcherState) -> Dict[str, Any]:
    """
    Build metadata filters from job requirements and overrides.
    
    Args:
        state: Current matcher state
        
    Returns:
        Updated state with metadata filters
    """
    if state.get("error"):
        return {}
    
    job_metadata = state.get("job_metadata", {})
    overrides = state.get("hard_constraints_overrides", {})
    
    # Build filters combining job metadata and overrides
    filters = {}
    
    # Required skills (MUST HAVE)
    required_skills = overrides.get("required_skills") or job_metadata.get("required_skills", [])
    if required_skills:
        filters["required_skills"] = required_skills
    
    # Minimum experience
    min_exp = overrides.get("min_experience_years") or job_metadata.get("min_experience_years")
    if min_exp is not None:
        filters["min_experience_years"] = min_exp
    
    # Seniority level
    seniority = overrides.get("seniority_level") or job_metadata.get("seniority_level")
    if seniority:
        # Accept same level or higher
        seniority_hierarchy = ["junior", "mid", "senior", "lead", "principal"]
        if seniority.lower() in seniority_hierarchy:
            idx = seniority_hierarchy.index(seniority.lower())
            filters["seniority_level"] = seniority_hierarchy[idx:]  # Current and above
    
    # Languages (from full_metadata if available)
    languages = overrides.get("languages") or job_metadata.get("full_metadata", {}).get("languages_required", [])
    if languages:
        filters["languages"] = languages
    
    # Remote type
    remote_type = overrides.get("remote_type") or job_metadata.get("remote_type")
    if remote_type:
        # Allow flexible matching - remote can work for hybrid, etc.
        if remote_type.lower() == "onsite":
            filters["remote_type"] = ["onsite", "hybrid"]
        elif remote_type.lower() == "hybrid":
            filters["remote_type"] = ["remote", "hybrid", "onsite"]
        elif remote_type.lower() == "remote":
            filters["remote_type"] = ["remote", "hybrid"]
    
    # Locations
    locations = overrides.get("locations") or job_metadata.get("locations", [])
    if locations:
        filters["locations"] = locations
    
    rag_logger.info(f"Built metadata filters: {filters}")
    
    return {
        "metadata_filters": filters
    }


async def hybrid_search_node(state: MatcherState, db: AsyncSession) -> Dict[str, Any]:
    """
    Perform hybrid search for candidates.
    
    Args:
        state: Current matcher state
        db: Database session
        
    Returns:
        Updated state with candidate results
    """
    if state.get("error"):
        return {}
    
    job_embedding = state.get("job_embedding")
    metadata_filters = state.get("metadata_filters", {})
    top_k = state.get("top_k", 20)
    
    if not job_embedding:
        return {
            "error": "Job embedding not available"
        }
    
    try:
        repo = HybridSearchRepository(db)
        
        # Perform hybrid search
        candidates = await repo.search_candidates(
            query_embedding=job_embedding,
            metadata_filters=metadata_filters,
            top_k=top_k,
            similarity_threshold=0.5  # Minimum 50% semantic similarity
        )
        
        rag_logger.info(f"Hybrid search found {len(candidates)} candidates")
        
        return {
            "candidate_results": candidates,
            "error": None,
        }
        
    except Exception as e:
        rag_logger.error(f"Hybrid search failed: {str(e)}")
        return {
            "error": f"Hybrid search failed: {str(e)}"
        }


def score_candidates_node(state: MatcherState) -> Dict[str, Any]:
    """
    Score and rank candidates based on match quality.
    
    Args:
        state: Current matcher state
        
    Returns:
        Updated state with scored candidates and summary
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
                "hard_constraints_applied": _format_constraints(state.get("metadata_filters", {}))
            }
        }
    
    # Score each candidate
    scored_candidates = []
    for result in candidate_results:
        candidate = result["candidate"]
        cv_metadata = result.get("cv_metadata", {})
        similarity_score = result["similarity_score"]
        
        # Calculate detailed match breakdown
        match_breakdown = _calculate_match_score(
            job_metadata=job_metadata,
            cv_metadata=cv_metadata,
            similarity_score=similarity_score
        )
        
        scored_candidates.append({
            "candidate_id": candidate.id,
            "cv_id": result["cv_id"],
            "name": cv_metadata.get("name") or candidate.name,
            "current_role": cv_metadata.get("current_role", "Not specified"),
            "match_score": match_breakdown["match_score"],
            "hybrid_similarity_score": similarity_score,
            "matched_skills": match_breakdown["matched_skills"],
            "missing_required_skills": match_breakdown["missing_required_skills"],
            "nice_to_have_skills_covered": match_breakdown["nice_to_have_covered"],
            "seniority_match": match_breakdown["seniority_match"],
            "experience": match_breakdown["experience"],
            "location_match": match_breakdown["location_match"],
            "language_match": match_breakdown["language_match"],
            "other_relevant_factors": match_breakdown["other_factors"],
            "overall_rationale": match_breakdown["rationale"],
        })
    
    # Sort by match_score descending
    scored_candidates.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Take top_k
    top_k = state.get("top_k", 10)
    final_matches = scored_candidates[:top_k]
    
    rag_logger.info(f"Scored {len(scored_candidates)} candidates, returning top {len(final_matches)}")
    
    # Build summary
    summary = {
        "role_title": job_metadata.get("title", "Unknown"),
        "primary_stack_or_domain": ", ".join(job_metadata.get("tech_stack", [])[:3]) or "General",
        "key_required_skills": job_metadata.get("required_skills", [])[:10],
        "nice_to_have_skills": job_metadata.get("preferred_skills", [])[:10],
        "hard_constraints_applied": _format_constraints(state.get("metadata_filters", {})),
    }
    
    return {
        "final_matches": final_matches,
        "summary": summary,
        "error": None,
    }


def _average_embeddings(embeddings: List[List[float]]) -> List[float]:
    """Average multiple embeddings into one."""
    if not embeddings:
        return []
    
    num_embeddings = len(embeddings)
    dim = len(embeddings[0])
    
    avg = [0.0] * dim
    for embedding in embeddings:
        for i, val in enumerate(embedding):
            avg[i] += val
    
    return [v / num_embeddings for v in avg]


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
