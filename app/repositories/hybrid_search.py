"""Hybrid search repository for CV matching with vector similarity + metadata filters."""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text, Text, Integer
from sqlalchemy.orm import joinedload
from app.db.models.cv import CV
from app.db.models.cv_embedding import CVEmbedding
from app.db.models.candidate import Candidate
from app.core.logging import rag_logger


class HybridSearchRepository:
    """Repository for hybrid search combining vector similarity and metadata filters."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def search_candidates(
        self,
        query_embedding: List[float],
        metadata_filters: Dict[str, Any],
        top_k: int = 20,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search: vector similarity + metadata filters.
        
        Args:
            query_embedding: Vector embedding of the job description
            metadata_filters: Dictionary of metadata filters to apply
            top_k: Maximum number of results to return
            similarity_threshold: Minimum cosine similarity score (0-1)
            
        Returns:
            List of candidate records with similarity scores
        """
        try:
            # Build metadata filter conditions
            filter_conditions = self._build_metadata_filters(metadata_filters)
            
            # Perform vector similarity search with metadata filters
            # Using pgvector's <=> operator for cosine distance
            # Note: cosine distance = 1 - cosine similarity
            query = (
                select(
                    CVEmbedding.cv_id,
                    func.avg(1 - CVEmbedding.embedding.cosine_distance(query_embedding)).label("similarity_score"),
                    CV,
                    Candidate
                )
                .join(CV, CVEmbedding.cv_id == CV.id)
                .join(Candidate, CV.candidate_id == Candidate.id)
                .where(
                    and_(
                        CV.is_processed == True,
                        *filter_conditions
                    )
                )
                .group_by(CVEmbedding.cv_id, CV.id, Candidate.id)
                .having(func.avg(1 - CVEmbedding.embedding.cosine_distance(query_embedding)) >= similarity_threshold)
                .order_by(text("similarity_score DESC"))
                .limit(top_k)
            )
            
            result = await self.db.execute(query)
            rows = result.all()
            
            # Format results
            candidates = []
            for row in rows:
                cv_id, similarity_score, cv, candidate = row
                candidates.append({
                    "candidate_id": candidate.id,
                    "cv_id": cv_id,
                    "similarity_score": float(similarity_score),
                    "candidate": candidate,
                    "cv": cv,
                    "cv_metadata": cv.structured_metadata or {},
                })
            
            rag_logger.info(f"Hybrid search returned {len(candidates)} candidates")
            return candidates
            
        except Exception as e:
            rag_logger.error(f"Hybrid search failed: {str(e)}")
            raise
    
    def _build_metadata_filters(self, metadata_filters: Dict[str, Any]) -> List:
        """
        Build SQLAlchemy filter conditions from metadata dictionary.
        
        Supports filters like:
        - required_skills: List[str] - candidate must have these skills
        - min_experience_years: int - candidate must have at least this experience
        - seniority_level: str or List[str] - acceptable seniority levels
        - languages: List[str] - required languages
        - remote_type: str or List[str] - work location preference
        - locations: List[str] - acceptable locations
        """
        conditions = []
        
        # Skills filter - candidate must have ALL required skills
        if "required_skills" in metadata_filters and metadata_filters["required_skills"]:
            required_skills = metadata_filters["required_skills"]
            if isinstance(required_skills, list) and required_skills:
                # Check if CV metadata contains all required skills
                # Use ->> to extract as text
                for skill in required_skills:
                    conditions.append(
                        func.cast(CV.structured_metadata.op('->>')('skills'), Text).ilike(f"%{skill}%")
                    )
        
        # Minimum experience filter
        if "min_experience_years" in metadata_filters:
            min_exp = metadata_filters["min_experience_years"]
            if min_exp is not None:
                # Use ->> to extract as text, then cast to integer
                conditions.append(
                    func.cast(
                        CV.structured_metadata.op('->>')('total_years_experience'),
                        Integer
                    ) >= min_exp
                )
        
        # Seniority level filter
        if "seniority_level" in metadata_filters:
            seniority = metadata_filters["seniority_level"]
            if seniority:
                if isinstance(seniority, list):
                    # Multiple acceptable seniority levels
                    seniority_conditions = [
                        func.cast(CV.structured_metadata.op('->>')('seniority_level'), Text).ilike(f"%{level}%")
                        for level in seniority
                    ]
                    conditions.append(or_(*seniority_conditions))
                else:
                    conditions.append(
                        func.cast(CV.structured_metadata.op('->>')('seniority_level'), Text).ilike(f"%{seniority}%")
                    )
        
        # Language filter - candidate must have at least one of the required languages
        if "languages" in metadata_filters and metadata_filters["languages"]:
            languages = metadata_filters["languages"]
            if isinstance(languages, list) and languages:
                language_conditions = [
                    func.cast(CV.structured_metadata.op('->>')('languages'), Text).ilike(f"%{lang}%")
                    for lang in languages
                ]
                conditions.append(or_(*language_conditions))
        
        # Remote type filter
        if "remote_type" in metadata_filters:
            remote_type = metadata_filters["remote_type"]
            if remote_type:
                if isinstance(remote_type, list):
                    remote_conditions = [
                        func.cast(CV.structured_metadata.op('->>')('location_type_preference'), Text).ilike(f"%{rt}%")
                        for rt in remote_type
                    ]
                    conditions.append(or_(*remote_conditions))
                else:
                    conditions.append(
                        func.cast(CV.structured_metadata.op('->>')('location_type_preference'), Text).ilike(f"%{remote_type}%")
                    )
        
        # Location filter - candidate location matches job locations
        if "locations" in metadata_filters and metadata_filters["locations"]:
            locations = metadata_filters["locations"]
            if isinstance(locations, list) and locations:
                location_conditions = [
                    or_(
                        func.cast(CV.structured_metadata.op('->>')('country'), Text).ilike(f"%{loc}%"),
                        func.cast(CV.structured_metadata.op('->>')('city'), Text).ilike(f"%{loc}%")
                    )
                    for loc in locations
                ]
                conditions.append(or_(*location_conditions))
        
        return conditions
