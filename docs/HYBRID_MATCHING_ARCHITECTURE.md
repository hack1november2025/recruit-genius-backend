# Hybrid Semantic Matching Architecture

## Overview

This document describes the comprehensive architecture for semantic matching between job descriptions and CVs (résumés) using hybrid search that combines vector embeddings with structured metadata.

## Technology Stack

- **Backend**: Python, FastAPI
- **AI/ML**: LangChain, LangGraph, OpenAI GPT-4o, OpenAI Embeddings
- **Database**: PostgreSQL with pgvector extension
- **Vector Dimension**: 1536 (OpenAI text-embedding-3-small)

## Architecture Components

### 1. Data Models

#### Core Models

**CV Model** (`cvs` table)
- Stores multiple CVs per candidate
- Tracks original and translated text
- Stores language detection results
- Contains structured metadata extracted by LLM
- Links to candidate via `candidate_id`

**Job Model** (`jobs` table)
- Stores job postings
- Contains full job description
- Links to job embeddings and metadata

**Candidate Model** (`candidates` table)
- Basic candidate information
- One-to-many relationship with CVs

#### Vector Storage Models

**CVEmbedding** (`cv_embeddings` table)
- Stores CV text chunks with vector embeddings
- Links to CV (not candidate) via `cv_id`
- Each CV chunked into ~500 tokens with 50 token overlap
- 1536-dimensional vectors for semantic search

**JobEmbedding** (`job_embeddings` table)
- Stores job description chunks with vector embeddings
- Links to job via `job_id`
- Same chunking strategy as CVs
- Enables semantic similarity search

#### Metadata Models

**CVMetrics** (`cv_metrics` table)
- Structured evaluation scores for CV-job matches
- Links to CV (not candidate) and optionally to job
- Stores:
  - Skills match score (0-100%)
  - Experience relevance score (0-10)
  - Education fit score (0-10)
  - Achievement impact score (0-10)
  - Keyword density score (0-100%)
  - Employment gap score (0-10, higher is better)
  - Readability score (0-10)
  - AI confidence score (0-100%)
  - Composite score (0-100)

**JobMetadata** (`job_metadata` table)
- Structured metadata extracted from job descriptions
- One-to-one with Job
- Contains:
  - Required/preferred skills
  - Experience requirements (min/max years)
  - Education requirements
  - Remote work type (remote/hybrid/onsite)
  - Locations
  - Seniority level
  - Salary range
  - Certifications
  - Responsibilities
  - Tech stack

### 2. Services

#### Translation Service
**Purpose**: Translate CVs to English for consistent processing

**Features**:
- Auto-detect language using `langdetect`
- Translate using GPT-4o-mini
- Preserve technical terms and formatting
- Track original language

**Location**: `app/services/translation_service.py`

#### CV Parser Service
**Purpose**: Extract text from PDF/DOCX files

**Features**:
- PDF text extraction using pypdf
- DOCX text extraction using python-docx
- Basic info extraction (name, email, phone)
- Skills detection using pattern matching

**Location**: `app/services/cv_parser.py`

#### Metadata Extraction Service (CV)
**Purpose**: Extract structured metadata from CV text using LLM

**Features**:
- Extracts: personal info, work experience, education, skills, certifications
- Calculates quality scores (gaps, readability, confidence)
- Uses GPT-4o with structured JSON output
- Handles date parsing and career progression analysis

**Location**: `app/services/metadata_extraction_service.py`

#### Job Metadata Extraction Service
**Purpose**: Extract structured metadata from job descriptions using LLM

**Features**:
- Extracts: required/preferred skills, experience, education, remote type
- Infers seniority level from job requirements
- Parses salary ranges and certifications
- Uses GPT-4o-mini for cost efficiency

**Location**: `app/services/job_metadata_extraction_service.py`

#### Embedding Service
**Purpose**: Generate vector embeddings for semantic search

**Features**:
- Uses OpenAI text-embedding-3-small (1536 dimensions)
- Chunks text into ~500 tokens with 50 token overlap
- Handles both single and batch embedding generation
- Token counting for optimization

**Location**: `app/services/embedding_service.py`

#### CV Processor Service
**Purpose**: Orchestrate CV processing workflow

**Features**:
- Integrates CV Parser Agent (LangGraph)
- Coordinates: extraction → translation → metadata → embeddings
- Stores results in database atomically
- Returns processing results

**Location**: `app/services/cv_processor.py`

#### Job Processing Service
**Purpose**: Process job descriptions with embeddings and metadata

**Features**:
- Extract job metadata using LLM
- Create embeddings for semantic search
- Store both in database
- Used after job description generation

**Location**: `app/services/job_processing_service.py`

### 3. LangGraph Agents

#### CV Parser Agent
**Purpose**: AI-powered workflow for processing uploaded CVs

**Workflow**:
1. **Extract Text Node**: Extract text from PDF/DOCX
2. **Translate Node**: Detect language and translate to English
3. **Extract Metadata Node**: Use LLM to extract structured data
4. **Create Embeddings Node**: Generate vectors and store in DB

**State Management**: Uses LangGraph StateGraph for workflow orchestration

**Location**: `app/agents/cv_parser/`

#### Job Generator Agent (Existing)
**Purpose**: Conversational AI job description generation

**Features**:
- Multi-turn conversation for job requirements gathering
- Generates professional job descriptions
- Uses LangGraph for stateful conversations
- Stores conversation history with PostgreSQL checkpointer

**Location**: `app/agents/job_generator/`

### 4. API Endpoints

#### CV Upload Endpoint
```
POST /api/v1/cvs/upload
```
- Accepts: PDF or DOCX file + candidate_id
- Returns: cv_id, original_language, extracted metadata
- Triggers full CV processing pipeline

**Location**: `app/api/routes/cvs.py`

#### Job Description Generation (Existing)
```
POST /api/v1/job-descriptions/chat
```
- Conversational job description generation
- Returns streaming markdown response

**Location**: `app/api/routes/job_descriptions.py`

## Hybrid Search Flow

### Phase 1: Data Ingestion

#### For CVs:
1. User uploads PDF/DOCX via `/api/v1/cvs/upload`
2. CV Parser Agent processes file:
   - Extract text
   - Detect language and translate to English
   - Extract structured metadata (LLM)
   - Generate embeddings (chunked)
3. Store in database:
   - CV record in `cvs` table
   - Embeddings in `cv_embeddings` table
   - Initially no metrics (calculated during matching)

#### For Jobs:
1. User generates job description via conversational AI
2. Job description saved to `jobs` table
3. Job Processing Service:
   - Extract metadata (LLM)
   - Generate embeddings (chunked)
4. Store in database:
   - Metadata in `job_metadata` table
   - Embeddings in `job_embeddings` table

### Phase 2: Matching (Future Implementation)

**Hybrid Search Strategy**:

1. **Semantic Search (Vector)**:
   ```sql
   SELECT cv_id, AVG(1 - (cv_embeddings.embedding <=> job_embeddings.embedding)) as semantic_score
   FROM cv_embeddings
   CROSS JOIN job_embeddings
   WHERE job_embeddings.job_id = ?
   GROUP BY cv_id
   ORDER BY semantic_score DESC
   LIMIT 100;
   ```

2. **Metadata Filtering**:
   - Filter by required skills match
   - Filter by experience range
   - Filter by education requirements
   - Filter by location/remote preference

3. **Scoring Components**:
   - **Semantic Score (40%)**: Cosine similarity from embeddings
   - **Skills Match (25%)**: Required skills coverage
   - **Experience Fit (15%)**: Years of experience alignment
   - **Education Fit (10%)**: Education level match
   - **Quality Score (10%)**: Employment gaps, readability, AI confidence

4. **Composite Scoring**:
   ```python
   composite_score = (
       semantic_score * 0.40 +
       skills_match * 0.25 +
       experience_fit * 0.15 +
       education_fit * 0.10 +
       quality_score * 0.10
   )
   ```

5. **Ranking**:
   - Sort by composite score DESC
   - Return top N candidates
   - Store match record in `matches` table

### Phase 3: Results

**Output**:
- List of top-N matched CVs for a job
- Each match includes:
  - Composite score
  - Breakdown of scoring components
  - Semantic similarity highlights
  - Skills match details
  - AI-generated reasoning

## Database Schema Changes

### New Tables
- `cvs`: Multiple CVs per candidate
- `job_embeddings`: Vector embeddings for jobs
- `job_metadata`: Structured job requirements

### Modified Tables
- `cv_embeddings`: Now references `cvs` instead of `candidates`
- `cv_metrics`: Now references `cvs` instead of `candidates`

### Migration
- File: `versions/effc88337b9a_add_cv_job_embeddings_job_metadata_.py`
- Drops old `cv_embeddings` and `cv_metrics`
- Recreates with new foreign key relationships
- Adds new tables: `cvs`, `job_embeddings`, `job_metadata`

## Key Design Decisions

### Why Multiple CVs per Candidate?
- Candidates may have multiple versions of their CV
- Different CVs for different roles/industries
- Track evolution of candidate profile over time
- Each CV gets its own embeddings and metrics

### Why Separate CV and Candidate Models?
- Candidate = person identity (name, email, contact)
- CV = document with specific content and metadata
- One candidate can have multiple CVs
- Cleaner separation of concerns

### Why Chunk Embeddings?
- OpenAI embedding models have token limits
- Chunking allows capturing different aspects of long documents
- Multiple vectors per document improve semantic search recall
- Overlap ensures context continuity

### Why LLM-based Metadata Extraction?
- More accurate than rule-based extraction
- Handles varied CV/job description formats
- Can infer implicit information (seniority, career progression)
- Flexible and adaptable to new requirements

### Why Hybrid Search?
- Pure semantic search can miss hard requirements
- Pure keyword search misses semantic similarity
- Combining both provides best of both worlds
- Metadata allows for business logic (required skills, experience ranges)

## Future Enhancements

### 1. Matching Engine Implementation
- Create `MatchingService` with hybrid search
- Implement vector similarity queries with pgvector
- Add metadata filtering logic
- Implement composite scoring algorithm

### 2. Real-time Matching
- Webhook/event system when new CV uploaded
- Automatically match against open jobs
- Notify recruiters of good matches

### 3. Match Explanations
- Use LLM to generate natural language explanations
- Highlight matching skills and experience
- Explain scoring breakdown
- Suggest improvements for candidates

### 4. Learning & Optimization
- Track recruiter feedback on matches
- Use feedback to tune scoring weights
- Improve metadata extraction prompts
- Fine-tune embedding model (future)

### 5. Advanced Features
- CV parsing improvements (tables, non-standard formats)
- Multi-language support (not just translation to English)
- Video/audio CV processing
- Integration with LinkedIn/GitHub profiles

## Usage Examples

### Upload and Process CV

```bash
curl -X POST "http://localhost:8000/api/v1/cvs/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@john_doe_cv.pdf" \
  -F "candidate_id=123"
```

Response:
```json
{
  "success": true,
  "cv_id": 456,
  "original_language": "en",
  "metadata": {
    "full_name": "John Doe",
    "email": "john@example.com",
    "years_of_experience": 5,
    "technical_skills": ["Python", "FastAPI", "PostgreSQL"],
    "education": [...],
    "work_experience": [...]
  }
}
```

### Generate Job Description (Existing)

```bash
curl -X POST "http://localhost:8000/api/v1/job-descriptions/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a job for a senior Python developer",
    "thread_id": "job-thread-123"
  }'
```

After job is created, embeddings and metadata are automatically extracted and stored.

## Running Migrations

```bash
# Apply migrations
cd /home/tjcode/workspace/hackathon-klx/backend
uv run alembic upgrade head

# Check migration status
uv run alembic current

# Rollback if needed
uv run alembic downgrade -1
```

## Dependencies

Required packages (add to `pyproject.toml` if missing):
- `langdetect`: Language detection
- `pypdf`: PDF text extraction
- `python-docx`: DOCX text extraction
- `pgvector`: PostgreSQL vector support
- All existing dependencies (langchain, openai, etc.)

## Testing

### Unit Tests
- Test individual services (translation, metadata extraction, etc.)
- Mock LLM calls for predictable results
- Test database operations with test database

### Integration Tests
- Test complete CV processing pipeline
- Test job processing pipeline
- Test vector similarity searches
- Test metadata filtering queries

### End-to-End Tests
- Upload real CV files
- Generate job descriptions
- Perform matching queries
- Validate results

## Monitoring & Logging

All services use structured logging:
- `llm_logger`: LLM-related operations
- `api_logger`: API requests/responses
- `rag_logger`: Embedding and vector operations
- `cv_parser_logger`: CV parsing operations

Log locations: `logs/` directory

## Security Considerations

1. **File Upload**: Validate file types and sizes
2. **Input Sanitization**: Sanitize CV text before LLM processing
3. **Rate Limiting**: Implement rate limits on CV uploads
4. **API Keys**: Store OpenAI API key securely in environment
5. **Database**: Use parameterized queries (SQLAlchemy handles this)

## Performance Considerations

1. **Chunking**: Balance chunk size vs. number of embeddings
2. **Batch Processing**: Batch embed multiple chunks together
3. **Database Indexes**: Ensure indexes on foreign keys and search fields
4. **Vector Search**: Use pgvector indexes (HNSW) for large datasets
5. **Caching**: Cache frequently accessed metadata
6. **Async**: All I/O operations are async for performance

## Conclusion

This architecture provides a robust foundation for semantic CV-job matching. The hybrid approach combines the power of vector embeddings for semantic similarity with structured metadata for precise filtering, resulting in high-quality candidate matches.

The system is designed to be:
- **Scalable**: Handle thousands of CVs and jobs
- **Accurate**: Combine multiple signals for matching
- **Flexible**: Easy to add new metadata fields or scoring components
- **Maintainable**: Clean separation of concerns, well-documented
- **Extensible**: Ready for future enhancements (learning, explanations, etc.)
