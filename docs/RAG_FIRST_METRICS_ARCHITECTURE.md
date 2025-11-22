# RAG-First Architecture with Comprehensive CV Metrics

## Overview

This document describes the refactored matching system that implements a **RAG-first approach** followed by **detailed AI-powered metrics calculation**. This architecture shifts from upfront filtering to broad semantic search followed by deep analysis.

## Architecture Changes

### Previous Architecture (Hybrid Search with Upfront Filtering)
```
Job → Embeddings → Metadata Filters → Vector Search + Filters → Score → Results
                      ↓
            (Too restrictive, 0 candidates found)
```

### New Architecture (RAG-First with Post-Search Metrics)
```
Job → Embeddings → Vector Search (wide net) → Calculate 8 Metrics → Score & Rank → Results
                         ↓                            ↓
                  (50+ candidates)              (Persisted to DB)
```

## Workflow Nodes

### 1. `retrieve_job_node`
- **Purpose**: Fetch job data, embeddings, and metadata
- **Unchanged**: Same as before

### 2. `rag_search_node` (formerly `hybrid_search_node`)
- **Purpose**: Perform pure vector similarity search
- **Changes**:
  - Removed all metadata filtering
  - Increased `top_k` from 20 to 50 (wider net)
  - Lowered similarity threshold to 0.5 (broader search)
  - Returns CV text in addition to metadata
- **Output**: 50+ semantically similar candidates

### 3. `calculate_metrics_node` (NEW)
- **Purpose**: Calculate comprehensive metrics for each CV-job pair
- **Process**:
  1. For each candidate from RAG search
  2. Calculate 8 detailed metrics using `CVMetricsCalculator`
  3. Persist metrics to `cv_metrics` table
  4. Attach metrics to candidate object
- **Metrics Calculated**:
  - **Core Fit** (3 metrics): Skills match, Experience relevance, Education fit
  - **Quality** (2 metrics): Achievement impact, Keyword density
  - **Risk/Confidence** (3 metrics): Employment gaps, Readability, AI confidence
  - **Composite**: Weighted combination of all metrics

### 4. `score_candidates_node`
- **Purpose**: Rank candidates by composite score
- **Changes**:
  - Uses persisted metrics instead of calculating ad-hoc scores
  - Returns all 8 metrics in response
  - Builds rationale from metrics
  - Caps final results at top 10 candidates

## CV Metrics Calculator

### Service: `app/services/cv_metrics_calculator.py`

#### Core Fit Metrics

**1. Skills Match Score (0-100%)**
- Direct matching of required skills
- Partial credit for skill variations (e.g., "python" in "python development")
- Formula: `(matched_skills + partial_matches * 0.5) / required_skills * 100`

**2. Experience Relevance Score (0-10)**
- **Years Component** (0-2.5): Ratio of candidate years to required years
- **Recency Component** (0-2.5): Recent experience weighted higher
- **Tech Stack Alignment** (0-2.5): Mentions of required tech in job history

**3. Education Fit Score (0-10)**
- **Degree Level** (0-6): PhD=6, Master=5, Bachelor=4, etc.
- **Certifications** (0-2): 0.5 points per certification
- **Requirement Match** (0-2): Direct match with required education

#### Quality Metrics

**4. Achievement Impact Score (0-10)**
- **Quantifiable Achievements**: Patterns like "20% increase", "$5M revenue"
- **Action Verbs**: "achieved", "led", "optimized" (0.2 each)
- **Metadata Achievements**: Structured achievement data (0.5 each)

**5. Keyword Density Score (0-100%)**
- Optimal range: 2-8% keyword density
- **Below 2%**: Linear scale 0-50 points
- **2-8%**: Linear scale 50-100 points (sweet spot)
- **Above 8%**: Penalized as keyword stuffing

#### Risk/Confidence Metrics

**6. Employment Gap Score (0-10, where 10 = no gaps)**
- Analyzes work history chronology
- **Gap > 6 months**: -0.5 points per month
- **Max penalty**: 3 points per gap

**7. Readability Score (0-10)**
- **Length**: Penalty for <200 words or >3000 words
- **Structure**: Requires 3+ standard sections
- **Sentence Complexity**: Avg 5-30 words per sentence
- **Formatting**: Caps ratio <30%

**8. AI Confidence Score (0-100%)**
- **Missing Critical Fields**: -15% per missing field (name, skills, experience)
- **Semantic Similarity**: 30% weight (high similarity = better extraction)
- **Incomplete Data**: -5% per incomplete work experience entry

### Composite Score Calculation

**Default Weights:**
- **Skills/Experience**: 40%
- **Education/Achievements**: 30%
- **Quality/Risk**: 30%

**Formula:**
```python
composite_score = (
    (skills_match * 0.5 + experience_relevance / 10 * 100 * 0.5) * 0.40 +
    (education_fit / 10 * 100 * 0.5 + achievement_impact / 10 * 100 * 0.5) * 0.30 +
    (keyword_density * 0.3 + employment_gap / 10 * 100 * 0.2 + 
     readability / 10 * 100 * 0.2 + ai_confidence * 0.3) * 0.30
)
```

## Database Schema

### `cv_metrics` Table
```sql
CREATE TABLE cv_metrics (
    id SERIAL PRIMARY KEY,
    cv_id INTEGER NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    
    -- Core Fit Metrics
    skills_match_score FLOAT NOT NULL,          -- 0-100%
    experience_relevance_score FLOAT NOT NULL,  -- 0-10
    education_fit_score FLOAT NOT NULL,         -- 0-10
    
    -- Quality Metrics
    achievement_impact_score FLOAT NOT NULL,    -- 0-10
    keyword_density_score FLOAT NOT NULL,       -- 0-100%
    
    -- Risk/Confidence Metrics
    employment_gap_score FLOAT NOT NULL,        -- 0-10
    readability_score FLOAT NOT NULL,           -- 0-10
    ai_confidence_score FLOAT NOT NULL,         -- 0-100%
    
    -- Composite
    composite_score FLOAT NOT NULL,             -- 0-100
    metric_details JSONB,                        -- Additional breakdown
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Repository Pattern

### `app/repositories/cv_metrics.py`

**Key Methods:**
- `upsert_metrics(cv_id, job_id, metrics_data)`: Create or update metrics
- `get_by_cv_and_job(cv_id, job_id)`: Retrieve specific CV-job metrics
- `get_top_candidates(job_id, min_score, limit)`: Get best matches for a job
- `get_by_cv_id(cv_id)`: All jobs a CV has been evaluated against
- `get_by_job_id(job_id)`: All CVs evaluated for a job

## API Response Format

### Before (Simple Scores)
```json
{
  "candidate_id": 1,
  "match_score": 75.5,
  "hybrid_similarity_score": 0.82,
  "matched_skills": ["Python", "Docker"],
  "missing_required_skills": ["Kubernetes"]
}
```

### After (Comprehensive Metrics)
```json
{
  "candidate_id": 1,
  "cv_id": 1,
  "name": "John Doe",
  "current_role": "Senior Python Developer",
  
  "match_score": 78.45,
  "hybrid_similarity_score": 0.82,
  
  "skills_match_score": 85.5,
  "experience_relevance_score": 8.2,
  "education_fit_score": 7.5,
  "achievement_impact_score": 6.5,
  "keyword_density_score": 72.0,
  "employment_gap_score": 9.0,
  "readability_score": 8.5,
  "ai_confidence_score": 92.0,
  
  "experience": {
    "total_years_experience": 8,
    "relevant_experience_years": 8,
    "relevant_summary": "Experienced Python developer..."
  },
  
  "overall_rationale": "Good overall match (78%). Strong skills alignment (86%). 8 years experience (relevance score: 8.2/10).",
  
  "metrics_details": {
    "semantic_similarity": 0.82,
    "weights_used": {
      "skills_experience": 0.40,
      "education_achievements": 0.30,
      "quality_risk": 0.30
    },
    "threshold_flags": {
      "skills_below_70": false,
      "confidence_below_80": false,
      "employment_gaps_detected": false
    }
  }
}
```

## Benefits of RAG-First Approach

### 1. **Broader Initial Search**
- Previous: 0 candidates due to strict filtering (required ALL 11 skills)
- Now: 50+ candidates based on semantic similarity

### 2. **Rich Analytical Data**
- Previous: Basic match score
- Now: 8 detailed metrics + rationale + confidence scores

### 3. **Persistent Metrics**
- Metrics saved to database for:
  - Historical analysis
  - ML model training
  - Reporting and analytics
  - Audit trails

### 4. **Flexible Ranking**
- Can re-rank without recalculating
- Can apply different weight configurations
- Can filter by specific metric thresholds post-search

### 5. **Better User Experience**
- Hiring managers see detailed breakdown
- Can understand *why* a candidate scores well/poorly
- Can identify specific skill gaps or strengths

## Configuration

### Adjustable Parameters

**Search Phase:**
```python
top_k = 50  # Number of candidates from RAG search
similarity_threshold = 0.5  # Minimum semantic similarity (0-1)
```

**Metrics Weights:**
```python
weights = {
    "skills_experience": 0.40,
    "education_achievements": 0.30,
    "quality_risk": 0.30
}
```

**Thresholds:**
```python
min_composite_score = 60.0  # Minimum overall match
min_confidence_score = 80.0  # Minimum AI confidence
max_employment_gaps = 2  # Max acceptable gaps
```

## Testing

### Test RAG Search
```bash
# Should return 50+ candidates
curl -X POST "http://localhost:8000/api/v1/jobs/1/match?top_k=10"
```

### Verify Metrics Persistence
```sql
-- Check metrics were saved
SELECT cv_id, job_id, composite_score, skills_match_score, ai_confidence_score
FROM cv_metrics
WHERE job_id = 1
ORDER BY composite_score DESC
LIMIT 10;
```

### Validate Metric Ranges
```sql
-- All metrics should be within valid ranges
SELECT 
    COUNT(*) as total,
    AVG(skills_match_score) as avg_skills,  -- Should be 0-100
    AVG(experience_relevance_score) as avg_exp,  -- Should be 0-10
    AVG(composite_score) as avg_composite  -- Should be 0-100
FROM cv_metrics;
```

## Migration Notes

### Breaking Changes
- **Removed**: `build_filters_node` from workflow
- **Renamed**: `hybrid_search_node` → `rag_search_node`
- **Added**: `calculate_metrics_node` to workflow
- **Response Schema**: Now includes 8 additional metric fields

### Backward Compatibility
- API endpoint unchanged: `POST /api/v1/jobs/{job_id}/match`
- Can still accept `hard_constraints_overrides` (currently ignored)
- Existing code calling matcher service will work but get expanded responses

## Performance Considerations

### Database Impact
- Each match request generates `top_k` (50) metric records
- Use upsert to avoid duplicates
- Consider partitioning `cv_metrics` table by `created_at` for large datasets

### Calculation Time
- Metrics calculation: ~50-100ms per CV
- For 50 candidates: ~2.5-5 seconds total
- Consider parallelization for production:
  ```python
  import asyncio
  metrics = await asyncio.gather(*[
      calculate_metrics_async(cv) for cv in candidates
  ])
  ```

### Caching Strategy
- Cache metrics for CV-job pairs
- Invalidate on CV or job update
- Use `cv_metrics.updated_at` for cache freshness

## Future Enhancements

1. **AI-Powered Rationale**: Use LLM to generate detailed natural language explanations
2. **Custom Weights**: Allow per-job custom metric weights
3. **Metric Trends**: Track how candidate scores change over time
4. **Comparative Analysis**: Side-by-side comparison of multiple candidates
5. **Feedback Loop**: Use hiring decisions to refine metric weights (ML)
6. **Explainable AI**: Visualize contribution of each metric to final score

## References

- Implementation: `app/services/cv_metrics_calculator.py`
- Repository: `app/repositories/cv_metrics.py`
- Workflow: `app/agents/matcher/graph.py`
- Nodes: `app/agents/matcher/nodes.py`
- Model: `app/db/models/cv_metrics.py`
