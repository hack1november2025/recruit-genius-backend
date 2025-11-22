# Job Processing - Quick Start Guide

## What Got Fixed? 🔧

**Problem:** Jobs were being created but `job_embeddings` and `job_metadata` tables stayed empty.

**Solution:** Integrated `JobProcessingService` into job creation to automatically generate:
- ✅ Vector embeddings (for semantic search)
- ✅ Structured metadata (for filtering)

---

## Quick Test

### 1. Check Current Status
```bash
uv run python test_job_processing.py
```

### 2. Create a Test Job
```bash
curl -X POST http://localhost:8000/api/v1/job-descriptions/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a senior Python developer job with FastAPI and PostgreSQL"
  }'
```

### 3. Verify Processing
```bash
# Check jobs endpoint
curl http://localhost:8000/api/v1/jobs

# Run test script again to see embeddings/metadata
uv run python test_job_processing.py
```

---

## Reprocess Existing Jobs

### Single Job
```bash
curl -X POST http://localhost:8000/api/v1/jobs/1/reprocess
```

### All Jobs (Batch)
```bash
curl -X POST http://localhost:8000/api/v1/jobs/batch-reprocess
```

Or use the interactive script:
```bash
uv run python test_job_processing.py
# Type 'y' when prompted
```

---

## What Gets Generated?

### For Each Job:
1. **Embeddings** (8-15 chunks typically)
   - 500-char text chunks with 50-char overlap
   - 1536-dimensional vectors (OpenAI)
   - Stored in `job_embeddings` table

2. **Metadata** (structured data)
   - Skills (required + preferred)
   - Experience (min/max years)
   - Location & remote type
   - Salary range
   - Seniority level
   - Tech stack
   - Stored in `job_metadata` table

---

## API Endpoints

### Job CRUD (with auto-processing)
```
POST   /api/v1/jobs              # Create job + process
GET    /api/v1/jobs              # List all jobs
GET    /api/v1/jobs/{id}         # Get single job
PATCH  /api/v1/jobs/{id}         # Update job
DELETE /api/v1/jobs/{id}         # Delete job
```

### Processing Endpoints (NEW!)
```
POST /api/v1/jobs/{id}/reprocess       # Reprocess single job
POST /api/v1/jobs/batch-reprocess      # Reprocess all jobs
```

### Conversational Job Creation
```
POST /api/v1/job-descriptions/chat     # Chat with agent
POST /api/v1/job-descriptions/chat/stream  # Streaming chat
```

---

## Files Modified

1. **`app/agents/job_generator/tools.py`**
   - Added `JobProcessingService` import
   - Added processing call after job creation
   - Enhanced success message with embedding count

2. **`app/api/routes/jobs.py`**
   - Added `JobProcessingService` import
   - Added processing to `create_job` endpoint
   - Added `reprocess_job` endpoint
   - Added `batch_reprocess_jobs` endpoint

3. **`test_job_processing.py`** (NEW)
   - Interactive test script
   - Status checking
   - Batch reprocessing

4. **`docs/JOB_PROCESSING_ARCHITECTURE.md`** (NEW)
   - Complete architecture documentation
   - Hybrid search strategy
   - Future enhancements

---

## Verification Checklist

- [ ] Tables exist: `job_embeddings`, `job_metadata`
- [ ] pgvector extension installed
- [ ] Environment variable `OPENAI_API_KEY` set
- [ ] Test script shows jobs with embeddings
- [ ] New jobs automatically get processed
- [ ] Reprocessing endpoints work

---

## Troubleshooting

### No embeddings after job creation?
```bash
# Check logs
tail -f logs/app.log

# Manually reprocess
curl -X POST http://localhost:8000/api/v1/jobs/1/reprocess
```

### Script shows empty tables?
```bash
# Check database connection
uv run python -c "from app.db.session import AsyncSessionLocal; import asyncio; asyncio.run(AsyncSessionLocal().__aenter__())"

# Check pgvector extension
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Processing fails?
- Check OpenAI API key is valid
- Check database has pgvector extension
- Review logs for specific errors
- Verify job description is not empty

---

## Next Steps

1. **Test the fix:** Run `test_job_processing.py`
2. **Backfill existing jobs:** Use batch reprocess endpoint
3. **Monitor processing:** Check logs for any failures
4. **Plan hybrid search:** Review `JOB_PROCESSING_ARCHITECTURE.md`

---

## Why This Matters

This processing pipeline enables **hybrid search** for matching:

```
Candidate Search → Hybrid Matching → Best Job Matches
                      ↓
    ┌─────────────────┴─────────────────┐
    │                                   │
Semantic Search              Structured Filters
(embeddings)                 (metadata)
    │                                   │
"Python backend"             • Remote: true
"API development"            • Experience: 3-5 years
"database design"            • Salary: >$100k
                             • Skills: [Python, FastAPI]
```

**Without processing → No search → No matches**

**With processing → Powerful hybrid search → Great matches** ✨
