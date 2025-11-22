# HR AI Recruitment Matcher Agent

## Overview

The **Matcher Agent** is an intelligent job-candidate matching system that uses **hybrid search** (semantic vector similarity + deterministic metadata filters) to find the best candidates for job openings.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                              │
│  POST/GET /api/v1/jobs/{job_id}/match                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Matcher Service                            │
│  - Orchestrates workflow execution                          │
│  - Persists results to database                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              LangGraph Workflow                             │
│  ┌─────────────────────────────────────────────┐            │
│  │ 1. retrieve_job_node                        │            │
│  │    - Fetch job + embeddings + metadata      │            │
│  └──────────────┬──────────────────────────────┘            │
│                 │                                            │
│  ┌──────────────▼──────────────────────────────┐            │
│  │ 2. build_filters_node                       │            │
│  │    - Extract hard constraints               │            │
│  └──────────────┬──────────────────────────────┘            │
│                 │                                            │
│  ┌──────────────▼──────────────────────────────┐            │
│  │ 3. hybrid_search_node                       │            │
│  │    - Vector similarity + metadata filters   │            │
│  └──────────────┬──────────────────────────────┘            │
│                 │                                            │
│  ┌──────────────▼──────────────────────────────┐            │
│  │ 4. score_candidates_node                    │            │
│  │    - Calculate match scores                 │            │
│  │    - Generate detailed rationale            │            │
│  └─────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Hybrid Search Repository                       │
│  - PostgreSQL with pgvector                                 │
│  - Cosine similarity search                                 │
│  - JSON metadata filtering                                  │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 1. Hybrid Search
- **Semantic Similarity**: Uses OpenAI embeddings (text-embedding-3-small) with pgvector
- **Metadata Filters**: Deterministic filtering on structured data
- **Configurable Threshold**: Minimum similarity score (default: 0.5)

### 2. Multi-Dimensional Scoring

Match score (0-100) based on:
- **Semantic Similarity (30%)**: Vector cosine similarity
- **Required Skills (40%)**: Percentage of required skills matched
- **Experience (15%)**: Years of experience vs. requirements
- **Seniority (10%)**: Alignment with job level
- **Nice-to-have Skills (5%)**: Bonus points for preferred skills

### 3. Hard Constraints (Filters)

Candidates failing these are excluded:
- Required skills
- Minimum experience years
- Seniority level
- Language requirements
- Location/remote type compatibility

### 4. Detailed Match Breakdown

For each candidate:
- Match score and semantic similarity
- Matched vs. missing required skills
- Seniority alignment (Exact/Overqualified/Underqualified)
- Experience details
- Location compatibility
- Language compatibility
- Clear rationale explaining the match

## Usage

### API Endpoint

#### POST `/api/v1/jobs/{job_id}/match`

**Request Body:**
```json
{
  "job_id": 42,
  "top_k": 10,
  "hard_constraints_overrides": {
    "required_skills": ["Python", "FastAPI"],
    "min_experience_years": 5,
    "seniority_level": ["senior", "lead"]
  },
  "persist_matches": true
}
```

**Response:**
```json
{
  "job_id": 42,
  "summary": {
    "role_title": "Senior Backend Engineer",
    "primary_stack_or_domain": "Python, FastAPI, PostgreSQL",
    "key_required_skills": ["Python", "FastAPI", "PostgreSQL", "REST APIs"],
    "nice_to_have_skills": ["Docker", "Kubernetes", "AWS"],
    "hard_constraints_applied": [
      "Skills: Python, FastAPI, PostgreSQL",
      "Min experience: 5+ years",
      "Seniority: Senior, Lead",
      "Location type: Remote or Hybrid"
    ]
  },
  "candidates": [
    {
      "candidate_id": 123,
      "name": "John Doe",
      "current_role": "Senior Backend Engineer",
      "match_score": 87.5,
      "hybrid_similarity_score": 0.89,
      "matched_skills": ["Python", "FastAPI", "PostgreSQL", "REST APIs"],
      "missing_required_skills": [],
      "nice_to_have_skills_covered": ["Docker", "AWS"],
      "seniority_match": "Exact",
      "experience": {
        "total_years_experience": 8,
        "relevant_experience_years": 6,
        "relevant_summary": "6 years building scalable backend systems..."
      },
      "location_match": {
        "job_location_type": "Remote",
        "candidate_location_type_preference": "Remote",
        "compatible": true,
        "notes": "Candidate prefers remote, job is remote"
      },
      "language_match": {
        "job_languages_required": ["English"],
        "candidate_languages": ["English - advanced", "Spanish - native"],
        "compatible": true
      },
      "other_relevant_factors": [
        "Available immediately",
        "Led teams of 5+ engineers"
      ],
      "overall_rationale": "Semantic similarity: 0.89. Matches 4/4 required skills. Exact for seniority level. 8 years experience (requires 5+)."
    }
  ]
}
```

#### GET `/api/v1/jobs/{job_id}/match?top_k=10`

Simplified GET endpoint with query parameters.

### Python Service Usage

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.matcher import MatcherService

async def find_candidates(db: AsyncSession, job_id: int):
    matcher = MatcherService(db)
    
    result = await matcher.find_matches_for_job(
        job_id=job_id,
        top_k=10,
        hard_constraints_overrides={
            "required_skills": ["Python", "FastAPI"],
            "min_experience_years": 5
        },
        persist_matches=True
    )
    
    return result
```

## Database Schema

### Required Tables

1. **jobs**: Job postings
2. **job_embeddings**: Vector embeddings of job descriptions
3. **job_metadata**: Structured job requirements
4. **candidates**: Candidate profiles
5. **cvs**: Candidate CVs/resumes
6. **cv_embeddings**: Vector embeddings of CVs
7. **matches**: Stored match results

### Key Fields in CV Metadata

The `cvs.structured_metadata` JSON field should contain:
```json
{
  "name": "John Doe",
  "current_role": "Senior Backend Engineer",
  "current_company": "Tech Corp",
  "seniority_level": "senior",
  "total_years_experience": 8,
  "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "primary_tech_stack": ["Python", "FastAPI"],
  "location_type_preference": "remote",
  "country": "USA",
  "city": "San Francisco",
  "time_zone": "PST",
  "languages": ["English - advanced", "Spanish - native"],
  "salary_expectation": "150000-180000 USD",
  "availability": "Immediately",
  "summary": "Senior backend engineer with 8 years..."
}
```

### Key Fields in Job Metadata

The `job_metadata` table stores:
- `required_skills`: List of must-have skills
- `preferred_skills`: Nice-to-have skills
- `min_experience_years`: Minimum years required
- `seniority_level`: Expected level (junior/mid/senior/lead)
- `remote_type`: onsite/hybrid/remote
- `locations`: Acceptable locations
- `tech_stack`: Technologies used
- `full_metadata`: Additional structured data

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/recruitgenius

# OpenAI for embeddings
OPENAI_API_KEY=sk-...

# Optional: LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls-...
LANGCHAIN_PROJECT=matcher-agent
```

### Adjustable Parameters

In `app/repositories/hybrid_search.py`:
- `similarity_threshold`: Minimum cosine similarity (default: 0.5)

In `app/agents/matcher/nodes.py`:
- Scoring weights for each dimension
- Seniority hierarchy
- Experience tolerance (currently 80%)

## Testing

### Run the Test Script

```bash
cd /home/tjcode/workspace/hackathon-klx/backend
uv run python test_matcher.py
```

### Prerequisites for Testing

1. Database with pgvector extension
2. At least one job with:
   - Embeddings in `job_embeddings`
   - Metadata in `job_metadata`
3. At least one candidate with:
   - CV in `cvs` table
   - Embeddings in `cv_embeddings`
   - Structured metadata in `cvs.structured_metadata`

## Error Handling

The agent handles errors gracefully:
- **Job not found**: Returns 404 error
- **No embeddings**: Returns error message
- **No candidates found**: Returns empty list with summary
- **Database errors**: Logged and returned as 500 error

Error state is tracked through the workflow and subsequent nodes are skipped if errors occur.

## Performance Considerations

### Optimization Tips

1. **Indexes**: Ensure indexes on:
   - `cv_embeddings.cv_id`
   - `job_embeddings.job_id`
   - `cvs.is_processed`
   - `job_metadata.job_id`

2. **Vector Index**: Create HNSW index for faster similarity search:
   ```sql
   CREATE INDEX ON cv_embeddings USING hnsw (embedding vector_cosine_ops);
   ```

3. **Batch Size**: Adjust `top_k` based on needs (1-50 recommended)

4. **Caching**: Consider caching job embeddings and metadata

## Future Enhancements

- [ ] Support for multi-language candidates
- [ ] Salary range matching
- [ ] Certifications filtering
- [ ] Custom scoring weight configuration per job
- [ ] Real-time re-ranking with LLM
- [ ] Explainable AI insights
- [ ] A/B testing for scoring algorithms

## Related Documentation

- [Hybrid Matching Architecture](./HYBRID_MATCHING_ARCHITECTURE.md)
- [Job Processing Architecture](./JOB_PROCESSING_ARCHITECTURE.md)
- [Quick Reference](./QUICK_REFERENCE.md)

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review error messages in API responses
3. Verify database schema and data
4. Check pgvector extension is installed
