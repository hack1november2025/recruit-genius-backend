# Implementation Guide: CV & Job Processing Refactor

## What Was Implemented

### 1. Database Schema Changes

**New Models**:
- `CV` model (`cvs` table) - Multiple CVs per candidate
- `JobEmbedding` model - Vector embeddings for job descriptions
- `JobMetadata` model - Structured job requirements

**Updated Models**:
- `CVEmbedding` - Now references `cv_id` instead of `candidate_id`
- `CVMetrics` - Now references `cv_id` instead of `candidate_id`

**Migration**: `versions/effc88337b9a_add_cv_job_embeddings_job_metadata_.py`

### 2. Services Created

| Service | Purpose | Location |
|---------|---------|----------|
| `TranslationService` | Translate CVs to English | `app/services/translation_service.py` |
| `MetadataExtractionService` | Extract CV metadata using LLM | `app/services/metadata_extraction_service.py` |
| `JobMetadataExtractionService` | Extract job metadata using LLM | `app/services/job_metadata_extraction_service.py` |
| `CVProcessorService` | Orchestrate CV processing | `app/services/cv_processor.py` |
| `JobProcessingService` | Process job descriptions | `app/services/job_processing_service.py` |

### 3. LangGraph Agent

**CV Parser Agent** (`app/agents/cv_parser/`)
- State: `state.py`
- Nodes: `nodes.py` (extract_text → translate → extract_metadata → create_embeddings)
- Graph: `graph.py`

### 4. API Endpoint

**CV Upload**: `POST /api/v1/cvs/upload`
- Accepts PDF/DOCX file + candidate_id
- Processes CV through agent pipeline
- Returns cv_id and extracted metadata

### 5. Documentation

- `docs/HYBRID_MATCHING_ARCHITECTURE.md` - Complete architecture guide

## Next Steps to Complete

### 1. Run Database Migration

```bash
cd /home/tjcode/workspace/hackathon-klx/backend
uv run alembic upgrade head
```

### 2. Install Missing Dependencies

Check if these are in `pyproject.toml`, if not add them:

```toml
[tool.uv.dependencies]
langdetect = "^1.0.9"
```

Install:
```bash
uv sync
```

### 3. Update Job Generator to Save Embeddings & Metadata

After a job is created via the conversational agent, process it:

```python
# In job_descriptions.py or wherever job is saved
from app.services.job_processing_service import JobProcessingService

# After creating job
job_processor = JobProcessingService()
await job_processor.process_job_description(
    job_id=job.id,
    job_description=job.description,
    db=db
)
```

### 4. Create Repositories (Optional but Recommended)

For better code organization:

- `CVRepository` in `app/repositories/cv.py`
- `JobEmbeddingRepository` in `app/repositories/job_embedding.py`
- `JobMetadataRepository` in `app/repositories/job_metadata.py`

### 5. Implement Matching Service (Future)

Create `app/services/matching_service.py`:
- Vector similarity search using pgvector
- Metadata filtering
- Composite scoring
- Return top-N matches

Example query structure:
```python
# Semantic search with pgvector
query = select(
    CVEmbedding.cv_id,
    func.avg(1 - CVEmbedding.embedding.cosine_distance(job_embedding)).label('similarity')
).join(
    JobEmbedding
).where(
    JobEmbedding.job_id == job_id
).group_by(
    CVEmbedding.cv_id
).order_by(
    desc('similarity')
).limit(100)
```

### 6. Update Match Model

Add fields for hybrid scoring:

```python
# In app/db/models/match.py
semantic_score = Column(Float, nullable=True)  # Vector similarity
metadata_score = Column(Float, nullable=True)  # Structured matching
composite_score = Column(Float, nullable=True)  # Final hybrid score
```

### 7. Testing

Create tests:
- `tests/test_cv_parser_agent.py`
- `tests/test_translation_service.py`
- `tests/test_metadata_extraction.py`
- `tests/test_cv_upload_api.py`

### 8. Environment Variables

Ensure `.env` has:
```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
```

## How to Use

### Upload and Process a CV

```bash
# Using curl
curl -X POST "http://localhost:8000/api/v1/cvs/upload" \
  -F "file=@path/to/cv.pdf" \
  -F "candidate_id=1"

# Using Python requests
import requests

files = {"file": open("cv.pdf", "rb")}
data = {"candidate_id": 1}
response = requests.post(
    "http://localhost:8000/api/v1/cvs/upload",
    files=files,
    data=data
)
print(response.json())
```

### Generate Job with Embeddings

1. Use existing conversational job generation endpoint
2. Job description is created
3. **TODO**: Automatically trigger job processing to create embeddings and metadata

## Architecture Benefits

### 1. Semantic Search
- Find similar CVs/jobs even with different wording
- "Python developer" matches "Python engineer", "Pythonista", etc.

### 2. Structured Filtering
- Hard requirements: "Must have 5+ years Python"
- Location matching
- Education requirements

### 3. Hybrid Scoring
- Combines semantic similarity with structured matching
- More accurate than either approach alone

### 4. Multi-CV Support
- Candidates can have multiple versions of their CV
- Each CV is independently embedded and searchable
- Track which CV was used for which application

### 5. Translation Support
- Accept CVs in any language
- Translate to English for consistent processing
- Track original language

### 6. Rich Metadata
- LLM extracts structured data from unstructured text
- Skills, experience, education, etc.
- Used for filtering and scoring

## Key Files Modified/Created

```
app/
├── agents/
│   └── cv_parser/              # NEW: LangGraph agent
│       ├── __init__.py
│       ├── graph.py
│       ├── nodes.py
│       └── state.py
├── api/
│   └── routes/
│       └── cvs.py              # NEW: CV upload endpoint
├── db/
│   └── models/
│       ├── cv.py               # NEW: CV model
│       ├── cv_embedding.py     # MODIFIED: Now references cv_id
│       ├── cv_metrics.py       # MODIFIED: Now references cv_id
│       ├── job_embedding.py    # NEW: Job embeddings
│       └── job_metadata.py     # NEW: Job metadata
├── schemas/
│   ├── cv.py                   # NEW: CV schemas
│   └── job_metadata.py         # NEW: Job metadata schemas
├── services/
│   ├── cv_processor.py         # NEW: CV processing orchestration
│   ├── job_processing_service.py  # NEW: Job processing
│   ├── metadata_extraction_service.py  # NEW: CV metadata extraction
│   ├── job_metadata_extraction_service.py  # NEW: Job metadata extraction
│   └── translation_service.py  # NEW: Translation
└── main.py                      # MODIFIED: Added cvs router

docs/
└── HYBRID_MATCHING_ARCHITECTURE.md  # NEW: Complete architecture guide

versions/
└── effc88337b9a_add_cv_job_embeddings_job_metadata_.py  # NEW: Migration
```

## Troubleshooting

### Migration Fails
- Check PostgreSQL is running
- Ensure pgvector extension is installed: `CREATE EXTENSION vector;`
- Check database user has permissions

### File Upload Fails
- Check file size limits
- Verify PDF/DOCX libraries are installed
- Check temp directory permissions

### Embedding Generation Fails
- Verify OpenAI API key is valid
- Check API rate limits
- Ensure sufficient credits

### Translation Fails
- Falls back to original text
- Check OpenAI API key
- Verify langdetect is installed

## Performance Tips

1. **Batch Processing**: Process multiple CVs in parallel
2. **Chunking**: Adjust chunk size based on content length
3. **Caching**: Cache frequently accessed metadata
4. **Indexes**: Ensure database indexes on foreign keys
5. **Vector Indexes**: Use HNSW indexes for large-scale vector search

## Security Notes

1. **File Validation**: Only PDF/DOCX allowed, validate file headers
2. **Size Limits**: Implement max file size (e.g., 10MB)
3. **Rate Limiting**: Limit CV uploads per user/IP
4. **Sanitization**: Clean extracted text before LLM processing
5. **API Keys**: Never commit API keys to git

## Questions?

See `docs/HYBRID_MATCHING_ARCHITECTURE.md` for detailed architecture documentation.
