# Matcher Agent Quick Start Guide

## Quick Test

### 1. Ensure Prerequisites
```bash
# Check database connection
psql -h localhost -U postgres -d recruitgenius -c "SELECT * FROM jobs LIMIT 1;"

# Check pgvector is installed
psql -h localhost -U postgres -d recruitgenius -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

### 2. Run the Test Script
```bash
cd /home/tjcode/workspace/hackathon-klx/backend
uv run python test_matcher.py
```

### 3. Test via API
```bash
# Start the server
uv run uvicorn app.main:app --reload --port 8000

# Test the endpoint (in another terminal)
curl -X POST "http://localhost:8000/api/v1/jobs/1/match" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "top_k": 5
  }'

# Or use GET method
curl "http://localhost:8000/api/v1/jobs/1/match?top_k=5"
```

## API Examples

### Basic Match Request
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/1/match" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "top_k": 10
  }'
```

### With Custom Constraints
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/1/match" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "top_k": 10,
    "hard_constraints_overrides": {
      "required_skills": ["Python", "FastAPI", "PostgreSQL"],
      "min_experience_years": 5,
      "seniority_level": ["senior", "lead"],
      "remote_type": ["remote", "hybrid"],
      "languages": ["English"]
    }
  }'
```

### Without Persisting Results
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/1/match" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "top_k": 10,
    "persist_matches": false
  }'
```

## Python Usage

### Simple Usage
```python
from app.services.matcher import MatcherService
from app.db.session import AsyncSessionLocal

async def find_matches():
    async with AsyncSessionLocal() as db:
        matcher = MatcherService(db)
        result = await matcher.find_matches_for_job(
            job_id=1,
            top_k=10
        )
        return result
```

### With Custom Filters
```python
result = await matcher.find_matches_for_job(
    job_id=1,
    top_k=10,
    hard_constraints_overrides={
        "required_skills": ["Python", "FastAPI"],
        "min_experience_years": 3,
        "seniority_level": ["mid", "senior"],
    },
    persist_matches=True
)
```

## Response Structure

### Success Response
```json
{
  "job_id": 1,
  "summary": {
    "role_title": "Backend Engineer",
    "primary_stack_or_domain": "Python, FastAPI",
    "key_required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "nice_to_have_skills": ["Docker", "AWS"],
    "hard_constraints_applied": [
      "Skills: Python, FastAPI, PostgreSQL",
      "Min experience: 3+ years"
    ]
  },
  "candidates": [
    {
      "candidate_id": 42,
      "name": "John Doe",
      "match_score": 87.5,
      "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
      "missing_required_skills": [],
      ...
    }
  ]
}
```

### Error Response
```json
{
  "detail": "Job with id 999 not found"
}
```

## Common Issues

### Issue: "No embeddings found for job"
**Solution:** Process the job first to generate embeddings
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/1/process"
```

### Issue: "No candidates found"
**Causes:**
1. No CVs in database
2. Hard constraints too strict
3. Similarity threshold too high

**Solutions:**
1. Add candidates/CVs and process them
2. Relax constraints in `hard_constraints_overrides`
3. Lower `similarity_threshold` in `hybrid_search.py`

### Issue: Empty matched_skills
**Cause:** Skills format mismatch in metadata

**Solution:** Ensure CV metadata has skills as list of strings:
```json
{
  "skills": ["Python", "FastAPI", "PostgreSQL"]
}
```

## Architecture Files

- `app/agents/matcher/state.py` - State schema
- `app/agents/matcher/nodes.py` - Workflow nodes
- `app/agents/matcher/graph.py` - LangGraph workflow
- `app/repositories/hybrid_search.py` - Vector + metadata search
- `app/services/matcher.py` - Orchestration service
- `app/api/routes/matcher.py` - API endpoints
- `app/schemas/matcher.py` - Request/response schemas

## Monitoring

### Check Logs
```bash
tail -f logs/app.log
```

### View Match Results
```sql
-- View stored matches
SELECT 
  m.id, m.job_id, m.candidate_id, m.match_score,
  j.title as job_title,
  c.name as candidate_name
FROM matches m
JOIN jobs j ON m.job_id = j.id
JOIN candidates c ON m.candidate_id = c.id
ORDER BY m.match_score DESC
LIMIT 10;
```

## Tuning Parameters

### Scoring Weights
Edit `app/agents/matcher/nodes.py`:
```python
weights = {
    "semantic": 30,        # Adjust importance of vector similarity
    "required_skills": 40, # Adjust importance of skills match
    "experience": 15,      # Adjust importance of experience
    "seniority": 10,       # Adjust importance of seniority
    "nice_to_have": 5      # Adjust importance of preferred skills
}
```

### Similarity Threshold
Edit `app/repositories/hybrid_search.py`:
```python
similarity_threshold=0.5  # Lower for more results, higher for stricter matching
```

### Top K Limit
In API request:
```json
{
  "top_k": 20  // Return up to 20 candidates (max: 50)
}
```

## Next Steps

1. ✅ Test basic matching
2. ✅ Review match scores and rationale
3. ✅ Adjust weights if needed
4. ✅ Add more constraints as needed
5. ✅ Integrate with frontend
6. ✅ Monitor performance
7. ✅ Fine-tune threshold and weights

## Documentation

- Full Guide: `docs/MATCHER_AGENT.md`
- Architecture: `docs/HYBRID_MATCHING_ARCHITECTURE.md`
- API Docs: `http://localhost:8000/docs`
