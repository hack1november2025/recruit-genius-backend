"""Service for calculating comprehensive CV metrics against job requirements."""
import re
from typing import Dict, Any, List
from datetime import datetime
from dateutil.parser import parse as parse_date
from app.core.logging import rag_logger


class CVMetricsCalculator:
    """
    Calculates comprehensive AI-powered metrics for CV evaluation.
    
    Metrics are divided into three categories:
    1. Core Fit Metrics: Direct job alignment (skills, experience, education)
    2. Quality Metrics: CV content depth (achievements, keyword density)
    3. Risk/Confidence Metrics: Potential issues (gaps, readability, AI confidence)
    """
    
    def __init__(self, weights: Dict[str, float] | None = None):
        """
        Initialize calculator with customizable weights.
        
        Args:
            weights: Custom weights for composite score calculation.
                    Default: skills/experience=40%, education/achievements=30%, quality/risk=30%
        """
        self.weights = weights or {
            "skills_experience": 0.40,
            "education_achievements": 0.30,
            "quality_risk": 0.30
        }
    
    def calculate_all_metrics(
        self,
        cv_metadata: Dict[str, Any],
        cv_text: str,
        job_metadata: Dict[str, Any],
        job_text: str,
        semantic_similarity: float
    ) -> Dict[str, Any]:
        """
        Calculate all metrics for a CV against a job.
        
        Args:
            cv_metadata: Structured CV metadata
            cv_text: Full CV text
            job_metadata: Job requirements metadata
            job_text: Full job description text
            semantic_similarity: Pre-computed semantic similarity score (0-1)
            
        Returns:
            Dictionary with all metric scores and detailed breakdown
        """
        # Core Fit Metrics
        skills_match_score = self._calculate_skills_match(
            cv_metadata.get("skills", []),
            job_metadata.get("required_skills", [])
        )
        
        experience_relevance_score = self._calculate_experience_relevance(
            cv_metadata.get("work_experience", []),
            cv_metadata.get("total_years_experience", 0),
            job_metadata.get("min_experience_years", 0),
            job_metadata.get("tech_stack", [])
        )
        
        education_fit_score = self._calculate_education_fit(
            cv_metadata.get("education", []),
            cv_metadata.get("certifications", []),
            job_metadata.get("required_education"),
            job_metadata.get("preferred_education")
        )
        
        # Quality Metrics
        achievement_impact_score = self._calculate_achievement_impact(cv_text, cv_metadata)
        
        keyword_density_score = self._calculate_keyword_density(
            cv_text,
            job_metadata.get("required_skills", []) + job_metadata.get("tech_stack", [])
        )
        
        # Risk/Confidence Metrics
        employment_gap_score = self._calculate_employment_gaps(
            cv_metadata.get("work_experience", [])
        )
        
        readability_score = self._calculate_readability(cv_text)
        
        ai_confidence_score = self._calculate_ai_confidence(cv_metadata, semantic_similarity)
        
        # Composite Score
        composite_score = self._calculate_composite_score(
            skills_match_score=skills_match_score,
            experience_relevance_score=experience_relevance_score,
            education_fit_score=education_fit_score,
            achievement_impact_score=achievement_impact_score,
            keyword_density_score=keyword_density_score,
            employment_gap_score=employment_gap_score,
            readability_score=readability_score,
            ai_confidence_score=ai_confidence_score
        )
        
        return {
            # Core Fit Metrics
            "skills_match_score": round(skills_match_score, 2),
            "experience_relevance_score": round(experience_relevance_score, 2),
            "education_fit_score": round(education_fit_score, 2),
            
            # Quality Metrics
            "achievement_impact_score": round(achievement_impact_score, 2),
            "keyword_density_score": round(keyword_density_score, 2),
            
            # Risk/Confidence Metrics
            "employment_gap_score": round(employment_gap_score, 2),
            "readability_score": round(readability_score, 2),
            "ai_confidence_score": round(ai_confidence_score, 2),
            
            # Composite
            "composite_score": round(composite_score, 2),
            
            # Detailed breakdown
            "metric_details": {
                "semantic_similarity": semantic_similarity,
                "weights_used": self.weights,
                "threshold_flags": {
                    "skills_below_70": skills_match_score < 70,
                    "confidence_below_80": ai_confidence_score < 80,
                    "employment_gaps_detected": employment_gap_score < 8
                }
            }
        }
    
    def _calculate_skills_match(
        self,
        cv_skills: List[str],
        required_skills: List[str]
    ) -> float:
        """
        Calculate skills match percentage (0-100%).
        Uses semantic matching to account for synonyms.
        """
        if not required_skills:
            return 100.0
        
        cv_skills_lower = {skill.lower().strip() for skill in cv_skills}
        required_skills_lower = {skill.lower().strip() for skill in required_skills}
        
        # Direct matches
        matched = cv_skills_lower & required_skills_lower
        
        # Partial matches (e.g., "python" in "python development")
        partial_matched = 0
        for req_skill in required_skills_lower:
            if req_skill not in matched:
                for cv_skill in cv_skills_lower:
                    if req_skill in cv_skill or cv_skill in req_skill:
                        partial_matched += 0.5  # Partial credit
                        break
        
        match_score = ((len(matched) + partial_matched) / len(required_skills_lower)) * 100
        return min(match_score, 100.0)
    
    def _calculate_experience_relevance(
        self,
        work_experience: List[Dict],
        total_years: int,
        min_required_years: int,
        tech_stack: List[str]
    ) -> float:
        """
        Calculate experience relevance score (0-10).
        Considers years, recency, and tech stack alignment.
        """
        score = 0.0
        
        # Handle None values
        total_years = total_years or 0
        min_required_years = min_required_years or 0
        work_experience = work_experience or []
        tech_stack = tech_stack or []
        
        # Years of experience (0-5 points)
        if min_required_years > 0:
            years_ratio = min(total_years / min_required_years, 2.0)
            score += years_ratio * 2.5
        else:
            # If no requirement, give credit based on total years
            score += min(total_years / 5.0, 2.5)
        
        # Recency weight (0-2.5 points) - recent experience is more valuable
        if work_experience:
            current_year = datetime.now().year
            most_recent = max(
                (exp.get("end_date") or str(current_year) for exp in work_experience),
                default=str(current_year)
            )
            try:
                recent_year = int(re.search(r'\d{4}', str(most_recent)).group())
                years_since = current_year - recent_year
                recency_score = max(0, 2.5 - (years_since * 0.5))
                score += recency_score
            except:
                score += 1.0  # Default if can't parse
        
        # Tech stack alignment (0-2.5 points)
        if tech_stack and work_experience:
            tech_mentions = 0
            for exp in work_experience:
                description = (exp.get("description", "") or "").lower()
                for tech in tech_stack:
                    if tech.lower() in description:
                        tech_mentions += 1
            
            tech_score = min(tech_mentions / len(tech_stack), 1.0) * 2.5
            score += tech_score
        
        return min(score, 10.0)
    
    def _calculate_education_fit(
        self,
        education: List[Dict],
        certifications: List[str],
        required_education: str | None,
        preferred_education: str | None
    ) -> float:
        """
        Calculate education fit score (0-10).
        Considers degree level, field relevance, and certifications.
        """
        score = 0.0
        
        if not education:
            return 3.0  # Minimum score if no education data
        
        # Degree level scoring (0-6 points)
        degree_levels = {
            "phd": 6.0, "doctorate": 6.0,
            "master": 5.0, "mba": 5.0, "ms": 5.0, "ma": 5.0,
            "bachelor": 4.0, "bs": 4.0, "ba": 4.0,
            "associate": 3.0,
            "diploma": 2.0, "certificate": 2.0
        }
        
        max_degree_score = 0.0
        for edu in education:
            degree = (edu.get("degree", "") or "").lower()
            for level, score_val in degree_levels.items():
                if level in degree:
                    max_degree_score = max(max_degree_score, score_val)
                    break
        
        score += max_degree_score
        
        # Certification bonus (0-2 points)
        cert_score = min(len(certifications) * 0.5, 2.0)
        score += cert_score
        
        # Requirement match (0-2 points)
        if required_education:
            req_lower = required_education.lower()
            for edu in education:
                degree = (edu.get("degree", "") or "").lower()
                if any(req_term in degree for req_term in req_lower.split()):
                    score += 2.0
                    break
        
        return min(score, 10.0)
    
    def _calculate_achievement_impact(
        self,
        cv_text: str,
        cv_metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate achievement impact score (0-10).
        Identifies and scores quantifiable accomplishments.
        """
        score = 0.0
        
        # Patterns for quantifiable achievements
        impact_patterns = [
            r'\d+%',  # Percentages (e.g., "increased by 20%")
            r'\$\d+[kmb]?',  # Money amounts
            r'\d+\s*(users|customers|clients)',  # User counts
            r'(led|managed|directed)\s+(\d+)',  # Team sizes
            r'(reduced|increased|improved|optimized).*?(\d+)',  # Improvement verbs
        ]
        
        cv_text_lower = cv_text.lower()
        
        for pattern in impact_patterns:
            matches = re.findall(pattern, cv_text_lower, re.IGNORECASE)
            score += min(len(matches) * 0.5, 2.0)
        
        # Check for action verbs
        action_verbs = [
            "achieved", "led", "managed", "developed", "implemented",
            "optimized", "increased", "reduced", "launched", "delivered"
        ]
        verb_count = sum(1 for verb in action_verbs if verb in cv_text_lower)
        score += min(verb_count * 0.2, 2.0)
        
        # Check metadata for achievements
        achievements = cv_metadata.get("achievements", [])
        if achievements:
            score += min(len(achievements) * 0.5, 2.0)
        
        return min(score, 10.0)
    
    def _calculate_keyword_density(
        self,
        cv_text: str,
        keywords: List[str]
    ) -> float:
        """
        Calculate keyword density score (0-100%).
        Normalized to avoid keyword stuffing.
        """
        if not keywords:
            return 50.0
        
        cv_text_lower = cv_text.lower()
        word_count = len(cv_text_lower.split())
        
        if word_count == 0:
            return 0.0
        
        total_keyword_count = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = cv_text_lower.count(keyword_lower)
            total_keyword_count += count
        
        # Calculate density (keywords per 100 words)
        density = (total_keyword_count / word_count) * 100
        
        # Optimal range: 2-8% keyword density
        # Too low: poor match, Too high: keyword stuffing
        if density < 2:
            score = (density / 2) * 50  # Scale 0-2% to 0-50
        elif density <= 8:
            score = 50 + ((density - 2) / 6) * 50  # Scale 2-8% to 50-100
        else:
            # Penalize excessive density (keyword stuffing)
            score = max(100 - (density - 8) * 10, 20)
        
        return min(score, 100.0)
    
    def _calculate_employment_gaps(
        self,
        work_experience: List[Dict]
    ) -> float:
        """
        Calculate employment gap score (0-10, where 10 = no gaps).
        Penalizes unexplained gaps > 6 months.
        """
        if not work_experience or len(work_experience) < 2:
            return 10.0  # No gaps detectable
        
        score = 10.0
        current_year = datetime.now().year
        
        try:
            # Sort by start date
            sorted_exp = sorted(
                work_experience,
                key=lambda x: self._parse_date(x.get("start_date", "")),
                reverse=True
            )
            
            for i in range(len(sorted_exp) - 1):
                current_end = self._parse_date(sorted_exp[i].get("end_date") or str(current_year))
                next_start = self._parse_date(sorted_exp[i + 1].get("start_date", ""))
                
                if current_end and next_start:
                    gap_months = (next_start.year - current_end.year) * 12
                    gap_months += next_start.month - current_end.month
                    
                    # Penalize gaps > 6 months
                    if gap_months > 6:
                        penalty = min((gap_months - 6) * 0.5, 3.0)
                        score -= penalty
        
        except Exception as e:
            rag_logger.warning(f"Error calculating employment gaps: {e}")
            return 8.0  # Default score if parsing fails
        
        return max(score, 0.0)
    
    def _calculate_readability(self, cv_text: str) -> float:
        """
        Calculate readability and structure score (0-10).
        Considers clarity, organization, and length.
        """
        score = 10.0
        
        # Length penalty (too short or too long)
        word_count = len(cv_text.split())
        if word_count < 200:
            score -= 2.0  # Too brief
        elif word_count > 3000:
            score -= 1.5  # Too verbose
        
        # Structure indicators (sections)
        sections = [
            "experience", "education", "skills", "summary",
            "objective", "projects", "certifications"
        ]
        section_count = sum(1 for section in sections if section in cv_text.lower())
        if section_count < 3:
            score -= 2.0  # Poorly structured
        
        # Sentence complexity (avg sentence length)
        sentences = re.split(r'[.!?]+', cv_text)
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_sentence_length > 30:
                score -= 1.0  # Too complex
            elif avg_sentence_length < 5:
                score -= 0.5  # Too simple
        
        # Formatting issues (excessive caps, special characters)
        caps_ratio = sum(1 for c in cv_text if c.isupper()) / max(len(cv_text), 1)
        if caps_ratio > 0.3:
            score -= 1.0  # Too much capitalization
        
        return max(score, 0.0)
    
    def _calculate_ai_confidence(
        self,
        cv_metadata: Dict[str, Any],
        semantic_similarity: float
    ) -> float:
        """
        Calculate AI confidence score (0-100%).
        Meta-metric on extraction reliability.
        """
        confidence = 100.0
        
        # Check for missing critical fields
        critical_fields = ["name", "skills", "total_years_experience"]
        missing_fields = sum(1 for field in critical_fields if not cv_metadata.get(field))
        confidence -= missing_fields * 15
        
        # Semantic similarity as confidence indicator
        # High similarity suggests good extraction
        confidence = (confidence * 0.7) + (semantic_similarity * 100 * 0.3)
        
        # Check for incomplete data
        if cv_metadata.get("work_experience"):
            incomplete_exp = sum(
                1 for exp in cv_metadata["work_experience"]
                if not exp.get("title") or not exp.get("company")
            )
            confidence -= incomplete_exp * 5
        
        return max(min(confidence, 100.0), 0.0)
    
    def _calculate_composite_score(
        self,
        skills_match_score: float,
        experience_relevance_score: float,
        education_fit_score: float,
        achievement_impact_score: float,
        keyword_density_score: float,
        employment_gap_score: float,
        readability_score: float,
        ai_confidence_score: float
    ) -> float:
        """
        Calculate composite score (0-100) using weighted averages.
        Default: 40% skills/experience, 30% education/achievements, 30% quality/risk
        """
        # Normalize all scores to 0-100 scale
        skills_exp_score = (
            (skills_match_score * 0.5) +  # Already 0-100
            ((experience_relevance_score / 10) * 100 * 0.5)  # Convert 0-10 to 0-100
        )
        
        edu_achieve_score = (
            ((education_fit_score / 10) * 100 * 0.5) +
            ((achievement_impact_score / 10) * 100 * 0.5)
        )
        
        quality_risk_score = (
            (keyword_density_score * 0.3) +  # Already 0-100
            ((employment_gap_score / 10) * 100 * 0.2) +
            ((readability_score / 10) * 100 * 0.2) +
            (ai_confidence_score * 0.3)  # Already 0-100
        )
        
        composite = (
            skills_exp_score * self.weights["skills_experience"] +
            edu_achieve_score * self.weights["education_achievements"] +
            quality_risk_score * self.weights["quality_risk"]
        )
        
        return min(composite, 100.0)
    
    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        try:
            # Try to extract year
            year_match = re.search(r'\d{4}', str(date_str))
            if year_match:
                year = int(year_match.group())
                # Try to extract month
                month_match = re.search(r'\d{1,2}', str(date_str))
                month = int(month_match.group()) if month_match else 1
                return datetime(year, month, 1)
        except:
            pass
        
        try:
            return parse_date(date_str)
        except:
            return None
