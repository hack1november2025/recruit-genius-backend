# Quick Reference: CV & Job Processing

## 🚀 Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Run Migration
```bash
uv run alembic upgrade head
```

### 3. Start Server
```bash
uv run uvicorn app.main:app --reload
```

## 📋 API Endpoints

### Upload CV
```bash
POST /api/v1/cvs/upload

# Example:
curl -X POST "http://localhost:8000/api/v1/cvs/upload" \
  -F "file=@cv.pdf"

# Response:
{
  "success": true,
  "cv_id": 123,
  "candidate_id": 45,
  "original_language": "en",
  "metadata": { ... }
}

# Notes:
# - No candidate_id needed in request
# - Email is extracted from CV
# - Existing candidate found by email or new one created
# - If no email: anonymous candidate created
```

### Generate Job Description (Existing)
```bash
POST /api/v1/job-descriptions/chat

# Example:
curl -X POST "http://localhost:8000/api/v1/job-descriptions/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a job for senior Python developer",
    "thread_id": "job-123"
  }'
```

## 🗂️ Database Tables

| Table | Purpose |
|-------|---------|
| `candidates` | Basic candidate info |
| `cvs` | CV documents (multiple per candidate) |
| `cv_embeddings` | Vector embeddings for CVs |
| `cv_metrics` | CV quality and match scores |
| `jobs` | Job postings |
| `job_embeddings` | Vector embeddings for jobs |
| `job_metadata` | Structured job requirements |
| `matches` | Candidate-job matches |

## 🔄 CV Processing Pipeline

```
1. Upload PDF/DOCX
   ↓
2. Extract Basic Info (email, name, phone)
   ↓
3. Find Candidate by Email OR Create New
   ↓
4. Extract Full Text (pypdf/python-docx)
   ↓
5. Detect Language (langdetect)
   ↓
6. Translate to English (GPT-4o-mini)
   ↓
7. Extract Metadata (GPT-4o)
   ↓
8. Generate Embeddings (OpenAI)
   ↓
9. Store in Database
```

## 🎯 Key Services

```python
# CV Processing
from app.services.cv_processor import CVProcessorService

processor = CVProcessorService()
result = await processor.process_cv(
    file_path="cv.pdf",
    candidate_id=1,
    db=db
)

# Job Processing
from app.services.job_processing_service import JobProcessingService

job_processor = JobProcessingService()
result = await job_processor.process_job_description(
    job_id=1,
    job_description="...",
    db=db
)
```

## 📊 Data Models

### CV Model
```python
cv = CV(
    candidate_id=1,
    original_text="...",
    translated_text="...",
    original_language="es",
    structured_metadata={...},
    is_processed=True
)
```

### Job Metadata Model
```python
job_metadata = JobMetadata(
    job_id=1,
    required_skills=["Python", "FastAPI"],
    min_experience_years=5,
    remote_type="hybrid",
    seniority_level="senior"
)
```

## 🔍 Future: Hybrid Search

```python
# Semantic Search (Vector)
SELECT cv_id, 
       AVG(1 - (embedding <=> job_embedding)) as similarity
FROM cv_embeddings
WHERE ...
GROUP BY cv_id

# + Metadata Filtering
WHERE required_skills @> metadata.skills
  AND experience_years >= min_experience_years

# = Hybrid Score
composite_score = 
  semantic * 0.40 +
  skills_match * 0.25 +
  experience_fit * 0.15 +
  education_fit * 0.10 +
  quality * 0.10
```

## 📁 Important Files

| File | Description |
|------|-------------|
| `app/agents/cv_parser/` | CV processing agent |
| `app/api/routes/cvs.py` | CV upload endpoint |
| `app/services/cv_processor.py` | CV orchestration |
| `app/services/job_processing_service.py` | Job processing |
| `app/db/models/cv.py` | CV database model |
| `docs/HYBRID_MATCHING_ARCHITECTURE.md` | Full architecture guide |

## 🐛 Troubleshooting

### Migration Fails
```bash
# Check PostgreSQL
psql -U postgres -d your_db

# Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

# Retry migration
uv run alembic upgrade head
```

### Import Errors
```bash
# Sync dependencies
uv sync

# Check if langdetect installed
uv pip list | grep langdetect
```

### Upload Fails
- Check file is PDF or DOCX
- Verify candidate_id exists
- Check OpenAI API key in .env
- Review logs in `logs/` directory

## 📝 Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname

# Optional
APP_NAME=HR Recruitment Backend
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run specific test
uv run pytest tests/test_cv_upload_api.py

# With coverage
uv run pytest --cov=app tests/
```

## 📚 Documentation

- **Architecture**: `docs/HYBRID_MATCHING_ARCHITECTURE.md`
- **Implementation**: `docs/IMPLEMENTATION_GUIDE.md`
- **Summary**: `docs/REFACTOR_SUMMARY.md`
- **This Guide**: `docs/QUICK_REFERENCE.md`

## 🎓 Key Concepts

**Vector Embeddings**: Numerical representations of text for semantic similarity

**Hybrid Search**: Combining semantic search (vectors) with structured filtering (metadata)

**Chunking**: Splitting long documents into smaller pieces for embedding

**LangGraph**: Framework for building stateful AI agents with workflows

**pgvector**: PostgreSQL extension for vector similarity search

## 🔗 Useful Commands

```bash
# Database
uv run alembic current              # Check migration status
uv run alembic upgrade head         # Apply migrations
uv run alembic downgrade -1         # Rollback one migration

# Development
uv run uvicorn app.main:app --reload --port 8000
uv run pytest -v                    # Verbose test output
uv run black app/                   # Format code
uv run ruff check app/              # Lint code

# Database queries (example)
psql -U postgres -d dbname -c "SELECT COUNT(*) FROM cvs;"
```

## 💡 Tips

1. **Always translate CVs to English** for consistent embeddings
2. **Chunk text at ~500 tokens** for optimal embedding quality
3. **Use async/await** for all I/O operations
4. **Batch embed** multiple chunks together for efficiency
5. **Index foreign keys** for faster queries
6. **Monitor OpenAI costs** - embeddings add up with many CVs

## 🚨 Common Mistakes

❌ Forgetting to run migrations
❌ Not installing langdetect dependency
❌ Missing OpenAI API key in .env
❌ Uploading non-PDF/DOCX files
❌ Not checking if candidate exists before upload
❌ Forgetting to process job descriptions after creation

✅ Follow the implementation guide step by step!
