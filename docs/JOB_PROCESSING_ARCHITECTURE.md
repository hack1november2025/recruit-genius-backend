# Job Processing Architecture - Embeddings & Metadata for Hybrid Search

## Overview

This document explains the **job processing pipeline** that generates **embeddings** and **metadata** for job descriptions. This infrastructure enables **hybrid search** (semantic + structured) when matching candidates with jobs.

## Problem That Was Fixed

### Issue
Job descriptions were being created but the `job_embeddings` and `job_metadata` tables remained empty because the processing service was never invoked.

### Root Cause
- Jobs were created via:
  1. Agent tool: `save_job_to_database` in `job_generator/tools.py`
  2. REST API: `POST /api/v1/jobs`
- Neither path called `JobProcessingService.process_job_description()`
- Processing service existed but was orphaned

### Solution
Integrated `JobProcessingService` into both job creation paths to automatically:
1. Generate vector embeddings (for semantic search)
2. Extract structured metadata (for filtered search)

---

## Architecture Components

### 1. Job Processing Service
**Location:** `app/services/job_processing_service.py`

**Responsibilities:**
- Orchestrates embedding generation and metadata extraction
- Manages database transactions
- Error handling and logging

**Process Flow:**
```python
async def process_job_description(job_id, job_description, db):
    1. Extract metadata using LLM (JobMetadataExtractionService)
    2. Create JobMetadata record with structured data
    3. Chunk job description into 500-char segments
    4. Generate embeddings for each chunk (EmbeddingService)
    5. Create JobEmbedding records
    6. Commit to database
```

### 2. Metadata Extraction Service
**Location:** `app/services/job_metadata_extraction_service.py`

**Purpose:** Uses LLM (GPT-4o-mini) to extract structured information from free-text job descriptions.

**Extracted Fields:**
- **Skills:** required_skills, preferred_skills, tech_stack
- **Experience:** min/max years
- **Education:** required/preferred levels
- **Location:** remote_type, locations
- **Seniority:** seniority_level, role_type
- **Compensation:** min/max salary, currency
- **Certifications:** required/preferred
- **Additional:** responsibilities, benefits

**Output Schema:** `JobMetadataStructure` (Pydantic model)

### 3. Embedding Service
**Location:** `app/services/embedding_service.py`

**Purpose:** Generates vector embeddings for semantic similarity search.

**Features:**
- Text chunking (500 chars, 50 char overlap)
- OpenAI text-embedding-3-small (1536 dimensions)
- Batch processing support

---

## Database Schema

### job_embeddings
```sql
CREATE TABLE job_embeddings (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,  -- pgvector type
    embedding_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_job_embeddings_job_id ON job_embeddings(job_id);
```

**Why Chunking?**
- Jobs can be long (2000+ words)
- Smaller chunks = more precise semantic matching
- 500-char chunks capture focused concepts

### job_metadata
```sql
CREATE TABLE job_metadata (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE UNIQUE,
    required_skills JSONB DEFAULT '[]',
    preferred_skills JSONB DEFAULT '[]',
    min_experience_years INTEGER,
    max_experience_years INTEGER,
    required_education VARCHAR(100),
    preferred_education VARCHAR(100),
    remote_type VARCHAR(50),  -- 'remote', 'hybrid', 'onsite'
    locations JSONB DEFAULT '[]',
    seniority_level VARCHAR(50),
    role_type VARCHAR(50),
    min_salary FLOAT,
    max_salary FLOAT,
    currency VARCHAR(10) DEFAULT 'USD',
    required_certifications JSONB DEFAULT '[]',
    preferred_certifications JSONB DEFAULT '[]',
    responsibilities JSONB DEFAULT '[]',
    benefits JSONB DEFAULT '[]',
    tech_stack JSONB DEFAULT '[]',
    full_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_job_metadata_job_id ON job_metadata(job_id);
CREATE INDEX idx_job_metadata_seniority ON job_metadata(seniority_level);
CREATE INDEX idx_job_metadata_remote_type ON job_metadata(remote_type);
```

---

## Integration Points

### 1. Agent Tool (Conversational Job Creation)
**File:** `app/agents/job_generator/tools.py`

```python
@tool
async def save_job_to_database(title, description, ...):
    async with AsyncSessionLocal() as db:
        # 1. Create job
        job = await repo.create(...)
        
        # 2. Process job (NEW!)
        processing_service = JobProcessingService()
        result = await processing_service.process_job_description(
            job_id=job.id,
            job_description=description,
            db=db
        )
        
        # 3. Return success with metadata count
        return f"✅ Job created! Generated {embeddings_count} embeddings"
```

### 2. REST API (Direct Job Creation)
**File:** `app/api/routes/jobs.py`

```python
@router.post("", response_model=JobResponse)
async def create_job(job: JobCreate, db: AsyncSession):
    # 1. Create job
    new_job = await repo.create(**job.model_dump())
    
    # 2. Process job (NEW!)
    processing_service = JobProcessingService()
    await processing_service.process_job_description(
        job_id=new_job.id,
        job_description=new_job.description,
        db=db
    )
    
    return new_job
```

---

## New API Endpoints

### 1. Reprocess Single Job
```http
POST /api/v1/jobs/{job_id}/reprocess
```

**Use Cases:**
- Job created before processing was implemented
- Processing failed initially
- Metadata schema updated and needs refresh

**Response:**
```json
{
  "job_id": 123,
  "embeddings_count": 8,
  "metadata": { ... },
  "message": "Job successfully reprocessed"
}
```

### 2. Batch Reprocess All Jobs
```http
POST /api/v1/jobs/batch-reprocess
```

**Use Cases:**
- Initial setup (backfill existing jobs)
- Bulk metadata refresh after schema changes

**Response:**
```json
{
  "total_jobs": 50,
  "processed": 45,
  "failed": 2,
  "skipped": 3,
  "errors": [
    {"job_id": 12, "error": "Invalid description"}
  ]
}
```

---

## Testing & Verification

### Test Script
**File:** `test_job_processing.py`

```bash
# Run interactive test
uv run python test_job_processing.py

# What it does:
# 1. Shows current processing status (jobs vs embeddings vs metadata)
# 2. Offers to reprocess all jobs
# 3. Shows detailed results per job
```

**Example Output:**
```
============================================================
📊 JOB PROCESSING STATUS
============================================================
Total Jobs: 5
Total Embeddings: 0
Total Metadata Records: 0

Job Processing Details:
------------------------------------------------------------
❌ Job #1: Senior Python Developer
   Embeddings: 0 | Metadata: 0
❌ Job #2: Frontend Engineer
   Embeddings: 0 | Metadata: 0
============================================================

Would you like to reprocess all jobs? (y/n):
```

### Manual API Testing

```bash
# 1. Create a job via agent (conversational)
curl -X POST http://localhost:8000/api/v1/job-descriptions/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a job for a senior data scientist with 5 years experience in ML"
  }'

# 2. Check if embeddings were created
curl http://localhost:8000/api/v1/jobs

# 3. Reprocess existing job
curl -X POST http://localhost:8000/api/v1/jobs/1/reprocess

# 4. Batch reprocess all jobs
curl -X POST http://localhost:8000/api/v1/jobs/batch-reprocess
```

---

## Hybrid Search Strategy (Future)

### Why Hybrid Search?

**Semantic Search (Embeddings):**
- ✅ Finds conceptually similar content
- ✅ Handles synonyms and paraphrasing
- ❌ Can't filter by exact criteria

**Structured Search (Metadata):**
- ✅ Precise filtering (e.g., "remote only", "5+ years exp")
- ✅ Fast indexed queries
- ❌ Misses semantic nuances

**Hybrid = Best of Both Worlds**

### Matching Algorithm (Candidate ↔ Job)

```python
async def hybrid_match(candidate_id: int, filters: dict):
    # 1. STRUCTURED FILTERING (Fast Pre-filter)
    query = select(Job).join(JobMetadata)
    
    # Apply hard filters from candidate requirements
    if filters.get("remote_only"):
        query = query.where(JobMetadata.remote_type == "remote")
    
    if filters.get("min_salary"):
        query = query.where(JobMetadata.min_salary >= filters["min_salary"])
    
    if filters.get("required_skills"):
        # JSONB contains operator
        query = query.where(
            JobMetadata.required_skills.contains(filters["required_skills"])
        )
    
    # 2. SEMANTIC MATCHING (Precision Ranking)
    candidate_embedding = get_candidate_embedding(candidate_id)
    
    # Use pgvector cosine similarity
    query = query.join(JobEmbedding).order_by(
        JobEmbedding.embedding.cosine_distance(candidate_embedding)
    ).limit(20)
    
    # 3. HYBRID SCORING
    for job in results:
        semantic_score = 1 - cosine_distance(...)
        metadata_score = calculate_metadata_match(candidate, job.metadata)
        
        # Weighted combination
        final_score = 0.6 * semantic_score + 0.4 * metadata_score
    
    return sorted_by_final_score
```

### Example Query

**Scenario:** Candidate is looking for:
- Remote Python jobs
- 3-5 years experience
- Salary > $100k
- Skills: Python, FastAPI, PostgreSQL

**SQL Query:**
```sql
WITH filtered_jobs AS (
  SELECT j.*, jm.* 
  FROM jobs j
  JOIN job_metadata jm ON j.id = jm.job_id
  WHERE 
    jm.remote_type = 'remote'
    AND jm.min_salary >= 100000
    AND jm.required_skills ?| ARRAY['Python', 'FastAPI', 'PostgreSQL']
    AND jm.min_experience_years <= 5
),
semantic_matches AS (
  SELECT 
    fj.*,
    je.embedding <=> :candidate_embedding AS semantic_distance
  FROM filtered_jobs fj
  JOIN job_embeddings je ON fj.id = je.job_id
  ORDER BY semantic_distance
  LIMIT 20
)
SELECT * FROM semantic_matches;
```

---

## Monitoring & Maintenance

### Health Checks

```python
# Check processing completeness
SELECT 
    j.id,
    j.title,
    COUNT(DISTINCT je.id) AS embedding_count,
    COUNT(DISTINCT jm.id) AS metadata_count
FROM jobs j
LEFT JOIN job_embeddings je ON j.id = je.job_id
LEFT JOIN job_metadata jm ON j.id = jm.job_id
GROUP BY j.id, j.title
HAVING 
    COUNT(DISTINCT je.id) = 0 
    OR COUNT(DISTINCT jm.id) = 0;
```

### Performance Metrics

- **Embedding Generation:** ~2-3 seconds per job
- **Metadata Extraction:** ~3-5 seconds per job (LLM call)
- **Total Processing:** ~5-8 seconds per job
- **Database Size:** ~10KB per job (embeddings + metadata)

### Troubleshooting

**Empty Tables After Job Creation:**
- ✅ FIXED: Processing now automatic on creation
- Check logs for processing errors
- Use reprocessing endpoints to backfill

**Slow Processing:**
- Consider batch processing during off-peak hours
- Use background tasks for large datasets
- Monitor OpenAI API rate limits

**Metadata Quality Issues:**
- Review LLM extraction prompts
- Adjust temperature (currently 0 for deterministic)
- Consider fine-tuning or using structured output mode

---

## Configuration

### Environment Variables

```env
# OpenAI (for embeddings and metadata extraction)
OPENAI_API_KEY=sk-...

# Database (PostgreSQL with pgvector)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
```

### Service Settings

**EmbeddingService:**
- Model: `text-embedding-3-small`
- Dimensions: 1536
- Chunk Size: 500 chars
- Overlap: 50 chars

**MetadataExtractionService:**
- Model: `gpt-4o-mini`
- Temperature: 0 (deterministic)
- Output: JSON structured

---

## Migration Guide

### For Existing Deployments

1. **Ensure pgvector is installed:**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Run Alembic migrations:**
   ```bash
   uv run alembic upgrade head
   ```

3. **Verify tables exist:**
   ```sql
   \dt job_embeddings
   \dt job_metadata
   ```

4. **Backfill existing jobs:**
   ```bash
   # Option 1: Python script
   uv run python test_job_processing.py
   
   # Option 2: API endpoint
   curl -X POST http://localhost:8000/api/v1/jobs/batch-reprocess
   ```

5. **Verify processing:**
   ```bash
   uv run python test_job_processing.py
   # All jobs should show ✅
   ```

---

## Future Enhancements

### Short Term
- [ ] Background task processing (FastAPI BackgroundTasks)
- [ ] Processing status tracking (processing, completed, failed)
- [ ] Retry logic for failed processing
- [ ] Processing queue for high-volume scenarios

### Medium Term
- [ ] Implement full hybrid search endpoint
- [ ] Add embedding similarity search endpoint
- [ ] Metadata-based filtering API
- [ ] Match scoring algorithm

### Long Term
- [ ] Real-time processing with webhooks
- [ ] A/B testing different embedding models
- [ ] Machine learning for match score optimization
- [ ] Analytics dashboard for match quality

---

## Related Documentation

- [HYBRID_MATCHING_ARCHITECTURE.md](./HYBRID_MATCHING_ARCHITECTURE.md) - Full matching system design
- [JOB_GENERATION_WORKFLOW.md](./JOB_GENERATION_WORKFLOW.md) - Conversational job creation
- [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) - General implementation patterns

---

## Support

For issues or questions:
1. Check logs: `logs/` directory
2. Run diagnostics: `test_job_processing.py`
3. Review recent changes: This document section "Problem That Was Fixed"
4. API endpoints: `/docs` (Swagger UI)
