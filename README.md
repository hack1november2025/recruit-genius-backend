<div align="center">

# 🚀 RecruitGenius AI

### Next-Generation AI-Powered Recruitment Platform

**Transform Your Hiring Process with Intelligent Automation**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python)](https://www.python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.45-FF6B6B?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791?style=for-the-badge&logo=postgresql)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com)

[**Features**](#-core-features) • [**Quick Start**](#-quick-start) • [**Architecture**](#-architecture) • [**Documentation**](#-documentation) • [**API**](#-api-reference)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Core Features](#-core-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [AI Agents](#-ai-agents)
- [API Reference](#-api-reference)
- [CV Processing Pipeline](#-cv-processing-pipeline)
- [Job Matching System](#-job-matching-system)
- [Development](#-development)
- [Deployment](#-deployment)
- [Documentation](#-documentation)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

**RecruitGenius AI** is a cutting-edge, AI-powered recruitment management platform that revolutionizes the hiring process through intelligent automation. Built with enterprise-grade technologies and powered by advanced LLMs, it combines conversational AI, vector-based semantic search, and comprehensive candidate evaluation to deliver unparalleled recruitment efficiency.

### Why RecruitGenius?

- 🤖 **Conversational AI** - Natural language interactions for job creation and candidate search
- 🎯 **Intelligent Matching** - Advanced 8-metric evaluation system for precise candidate-job alignment
- 📊 **RAG-Powered Search** - Semantic search across your entire CV database using pgvector
- 🌍 **Multi-Language Support** - Automatic translation of CVs in any language to English
- 📈 **Real-Time Analytics** - Comprehensive dashboard with recruitment metrics and insights
- 🔄 **Automated Workflow** - End-to-end automation from CV upload to candidate ranking
- 🐳 **Production-Ready** - Fully containerized with Docker, health checks, and monitoring

### Perfect For

- **Recruitment Agencies** - Scale your operations with AI-powered candidate matching
- **HR Departments** - Streamline hiring workflows and reduce time-to-hire
- **Startups** - Build your team efficiently with limited HR resources
- **Enterprise** - Handle high-volume recruitment with consistent quality

---

## ✨ Core Features

### 1. 🤖 AI-Powered Job Description Generator

Generate comprehensive, professional job postings from simple descriptions using conversational AI.

**Features:**
- 💬 Natural language interface - just describe what you need
- 🔄 Iterative refinement - modify jobs through conversation
- 🎨 Multiple tone options - formal, friendly, or inclusive
- ✅ Bias detection and inclusive language suggestions
- 💾 Direct database integration with save commands
- 📝 Structured output with responsibilities, requirements, and benefits

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/job-descriptions/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a job for a senior Python backend engineer with AWS experience"
  }'
```

### 2. 📄 Intelligent CV Processing

Advanced CV parsing with automatic language detection, translation, and metadata extraction.

**Pipeline:**
1. **Upload** - Support for PDF and DOCX formats
2. **Text Extraction** - High-quality text extraction from documents
3. **Language Detection** - Automatic detection of 50+ languages
4. **Translation** - Automatic translation to English for consistency
5. **Metadata Extraction** - LLM-powered extraction of skills, experience, education
6. **Embedding Generation** - OpenAI text-embedding-3-small for semantic search
7. **Storage** - Structured storage with vector embeddings

**Features:**
- 🌍 Multi-language support with automatic translation
- 🔍 Smart candidate matching by email
- 📊 Automatic chunking for large CVs
- 🎯 Vector embeddings for semantic search
- 📈 Quality scoring and validation

### 3. 🎯 Advanced Job Matching System

State-of-the-art RAG-first matching with comprehensive 8-metric evaluation.

**8 Core Metrics:**

| Metric | Weight | Description |
|--------|--------|-------------|
| **Skills Match** | 25% | Semantic + keyword matching of required skills |
| **Experience Relevance** | 20% | Years of experience in relevant roles |
| **Education Fit** | 15% | Degree level and field alignment |
| **Achievement Impact** | 15% | Quantifiable accomplishments and outcomes |
| **Keyword Density** | 10% | Relevant terminology presence |
| **Employment Gap** | 5% | Career continuity assessment |
| **Readability** | 5% | CV structure and clarity |
| **AI Confidence** | 5% | Extraction reliability score |

**Composite Score Formula:**
```python
composite = (
    skills_match * 0.25 +
    experience_relevance * 0.20 +
    education_fit * 0.15 +
    achievement_impact * 0.15 +
    keyword_density * 0.10 +
    employment_gap * 0.05 +
    readability * 0.05 +
    ai_confidence * 0.05
) # Result: 0-100
```

### 4. 💬 RAG-Powered CV Chat Interface

Conversational interface to query your CV database using natural language.

**Capabilities:**
- 🔍 Semantic search across all CVs
- 💬 Natural language queries (e.g., "Find Java developers in London")
- 🧠 Context-aware conversations with memory
- 📊 Structured candidate summaries
- 🔗 Direct candidate profile links
- 💾 Persistent conversation history

**Architecture:**
- **LangGraph ReAct Agent** - Autonomous reasoning and tool use
- **PostgreSQL Checkpointing** - Conversation state persistence
- **Tool-Based RAG** - LLM decides when to retrieve information
- **Vector Search** - pgvector for semantic similarity

---

## 🛠 Tech Stack

### Core Framework
- **FastAPI 0.115+** - High-performance async Python web framework
- **Python 3.11+** - Modern Python with type hints and async/await
- **Uvicorn** - Lightning-fast ASGI server
- **Pydantic 2.9+** - Data validation and settings management

### AI & Machine Learning
- **LangChain 0.3.7** - LLM orchestration and chain building
- **LangGraph 0.2.45** - Stateful AI agent workflows with checkpointing
- **OpenAI GPT-4o** - Advanced language model for generation and analysis
- **OpenAI text-embedding-3-small** - Efficient text embeddings
- **tiktoken** - Token counting and text chunking

### Database & Storage
- **PostgreSQL 16** - Robust relational database
- **pgvector** - Vector similarity search extension
- **SQLAlchemy 2.0+** - Async ORM with advanced features
- **Alembic 1.13+** - Database migration management
- **asyncpg** - High-performance PostgreSQL driver

### Document Processing
- **pypdf 4.0+** - PDF text extraction
- **python-docx 1.1+** - DOCX document parsing
- **langdetect 1.0.9** - Language detection for 50+ languages
- **python-magic** - File type detection

### Development Tools
- **Docker & Docker Compose** - Containerization and orchestration
- **pytest** - Testing framework
- **black** - Code formatting
- **ruff** - Fast Python linter
- **uv** - Modern Python package manager

---

## ⚡ Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **OpenAI API Key**

### Option 1: Docker Deployment (Recommended) 🐳

The fastest way to get RecruitGenius running:

```bash
# 1. Clone the repository
git clone <repository-url>
cd backend

# 2. Create .env file with your OpenAI API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-your-key-here

# 3. Start everything with one command
docker compose up -d

# 4. Wait for health checks (~30 seconds)
docker compose logs -f app

# ✅ Ready when you see: "Application startup complete"
```

**Access the application:**
- 🌐 **API**: http://localhost:8000
- 📚 **Documentation**: http://localhost:8000/docs
- ✅ **Health Check**: http://localhost:8000/api/v1/health
- 🗄️ **pgAdmin**: http://localhost:5050 (admin@recruitgenius.com / admin)

**Useful Docker commands:**
```bash
# View logs
docker compose logs -f app

# Stop services
docker compose down

# Rebuild after code changes
docker compose up -d --build

# View container status
docker compose ps

# Access database shell
docker compose exec db psql -U postgres -d recruitment
```

### Option 2: Local Development 💻

For development with hot-reload:

```bash
# 1. Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Start database with Docker
docker compose up -d db pgadmin

# 3. Install Python dependencies
uv sync

# 4. Create .env file
cp .env.example .env
# Edit .env and configure:
# - OPENAI_API_KEY=sk-your-key-here
# - DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/recruitment

# 5. Enable pgvector extension
docker compose exec db psql -U postgres -d recruitment -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 6. Run database migrations
uv run alembic upgrade head

# 7. Start development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify installation:**
```bash
# Check migration status
uv run alembic current

# Test API
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status": "healthy", "database": "connected"}
```

---

## 🏗 Architecture

RecruitGenius follows a clean, layered architecture optimized for AI agent workflows:

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                      │
└─────────────────────────────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│  API Routes  │        │  AI Agents   │        │   Services   │
│              │        │              │        │              │
│ • Health     │◄───────│ • CV Parser  │───────►│ • CV Proc.   │
│ • CVs        │        │ • Job Gen    │        │ • Embedding  │
│ • Jobs       │        │ • Matcher    │        │ • Translation│
│ • Matcher    │        │ • CV Chat    │        │ • Metrics    │
│ • Chat       │        │              │        │ • RAG        │
└──────────────┘        └──────────────┘        └──────────────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 ▼
                        ┌──────────────┐
                        │ Repositories │
                        │              │
                        │ • Base CRUD  │
                        │ • Candidate  │
                        │ • CV         │
                        │ • Job        │
                        │ • Match      │
                        │ • Vector Ops │
                        └──────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│ PostgreSQL   │        │   pgvector   │        │  OpenAI API  │
│              │        │              │        │              │
│ • Structured │        │ • Embeddings │        │ • GPT-4o     │
│   Data       │        │ • Semantic   │        │ • Embeddings │
│ • Relations  │        │   Search     │        │ • Chat       │
└──────────────┘        └──────────────┘        └──────────────┘
```

### Project Structure

```
backend/
├── app/
│   ├── agents/                    # 🤖 LangGraph AI Agents
│   │   ├── cv_parser/            # CV processing workflow
│   │   ├── job_generator/        # Conversational job creation
│   │   ├── matcher/              # RAG-first candidate matching
│   │   └── cv_chat/              # Conversational CV search
│   ├── api/                       # 🌐 REST API Layer
│   │   └── routes/               # API endpoints
│   ├── services/                  # 💼 Business Logic
│   ├── repositories/              # 🗄️ Data Access Layer
│   ├── db/                        # 🗃️ Database Layer
│   │   └── models/               # SQLAlchemy models
│   ├── schemas/                   # 📋 Pydantic Schemas
│   ├── core/                      # ⚙️ Core Configuration
│   └── main.py                    # 🚀 Application entry point
├── alembic/                       # 🔄 Database Migrations
├── docs/                          # 📚 Documentation
├── specifications/                # 📝 Requirements
├── tests/                         # 🧪 Test Suite
├── docker-compose.yml             # 🐳 Docker orchestration
├── Dockerfile                     # 🐳 Container image
├── pyproject.toml                 # 📦 Dependencies
└── README.md                      # 📖 This file
```

---

## 🤖 AI Agents

RecruitGenius uses **LangGraph** to implement sophisticated AI agents with state management and workflow orchestration.

### 1. CV Parser Agent

**Purpose:** Process uploaded CVs through a multi-stage pipeline.

**Workflow:**
```
START → Extract Text → Detect Language → Translate → 
Extract Metadata → Generate Embeddings → END
```

**Key Features:**
- Supports PDF and DOCX files
- Automatic language detection (50+ languages)
- Translation to English for consistency
- LLM-powered metadata extraction
- Vector embedding generation

### 2. Job Generator Agent

**Purpose:** Conversational job description creation with iterative refinement.

**Pattern:** ReAct (Reasoning + Acting)

**Features:**
- 💬 Multi-turn conversations with context
- 🧠 PostgreSQL checkpointing for persistence
- 🔄 Iterative refinement
- 💾 Direct save to database via tool calling

### 3. Matcher Agent

**Purpose:** RAG-first candidate matching with comprehensive evaluation.

**Workflow:**
```
START → Retrieve Job → RAG Search → Calculate Metrics → 
Score Candidates → END
```

**Features:**
- 🎯 Vector similarity search first
- 📊 Comprehensive 8-metric evaluation
- 🔄 Configurable top_k results
- 🚨 Error handling at each step

### 4. CV Chat Agent

**Purpose:** Conversational interface for CV database queries.

**Pattern:** ReAct Agent with Tool Calling

**Features:**
- 🔍 Autonomous tool usage
- 💾 PostgreSQL checkpointing for conversation memory
- 🎯 Context-aware responses
- 📊 Structured candidate summaries

---

## 📡 API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Health & Status

#### `GET /health`
System health check.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-11-22T10:30:00Z"
}
```

---

### CV Management

#### `POST /cvs/upload`
Upload and process a CV.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/cvs/upload" \
  -F "file=@john_doe_cv.pdf"
```

**Response:**
```json
{
  "success": true,
  "cv_id": 123,
  "candidate_id": 45,
  "original_language": "es",
  "metadata": {
    "name": "John Doe",
    "email": "john@example.com",
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "experience_years": 5
  },
  "embeddings_created": true
}
```

---

### Job Description Generation

#### `POST /job-descriptions/chat`
Conversational job description generation.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/job-descriptions/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a job for a senior backend engineer with Python and AWS"
  }'
```

**Response:**
```json
{
  "thread_id": "job-abc123",
  "response": "# Senior Backend Engineer\n\n## About the Role\n...",
  "job_saved": false
}
```

---

### Candidate Matching

#### `POST /matcher/match`
Match candidates to a job using AI.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/matcher/match" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 42,
    "top_k": 10
  }'
```

**Response:**
```json
{
  "job_id": 42,
  "summary": {
    "total_candidates_evaluated": 10,
    "avg_match_score": 72.5
  },
  "candidates": [
    {
      "candidate_id": 15,
      "name": "Jane Smith",
      "composite_score": 87.5,
      "metrics": {
        "skills_match_score": 92.0,
        "experience_relevance_score": 8.5,
        "education_fit_score": 9.0
      }
    }
  ]
}
```

---

### CV Chat Interface

#### `POST /chat`
Query CV database using natural language.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find me Python developers with 5+ years experience"
  }'
```

**Response:**
```json
{
  "thread_id": "chat-xyz789",
  "response_text": "I found 12 Python developers with 5+ years of experience...",
  "structured_response": {
    "type": "chat_response",
    "agent_used_tools": true
  }
}
```

---

## 🔄 CV Processing Pipeline

Comprehensive workflow for CV ingestion and analysis:

```
Upload CV (PDF/DOCX)
    ↓
1. File Validation (type, size, integrity)
    ↓
2. Text Extraction (PyPDF/python-docx)
    ↓
3. Quick Metadata Extraction (email, name, phone)
    ↓
4. Candidate Matching/Creation (by email)
    ↓
5. Language Detection (langdetect - 50+ languages)
    ↓
6. Translation to English (GPT-4o-mini)
    ↓
7. Comprehensive Metadata Extraction (LLM)
    ↓
8. Text Chunking (500 tokens, 50 overlap)
    ↓
9. Embedding Generation (OpenAI)
    ↓
10. Database Storage (PostgreSQL + pgvector)
    ↓
CV Ready for Matching
```

---

## 🎯 Job Matching System

### RAG-First Architecture

```
1. Wide Net Retrieval (RAG)
   ↓
2. Comprehensive Evaluation (8 Metrics)
   ↓
3. Intelligent Ranking (Composite Scores)
```

### Matching Workflow

```
Job Posted
    ↓
Step 1: Job Processing
    • Extract job description text
    • Generate job embeddings
    • Extract structured metadata
    ↓
Step 2: RAG Retrieval (Semantic Search)
    • Vector similarity search (pgvector)
    • Top-K candidates (e.g., 50)
    • No hard filters - wide net
    ↓
Step 3: Metric Calculation (All 8 Metrics)
    • Skills Match (25%)
    • Experience Relevance (20%)
    • Education Fit (15%)
    • Achievement Impact (15%)
    • Keyword Density (10%)
    • Employment Gap (5%)
    • Readability (5%)
    • AI Confidence (5%)
    ↓
Step 4: Score Aggregation
    • Calculate weighted composite score
    • Normalize to 0-100 range
    ↓
Step 5: Ranking & Filtering
    • Sort by composite score
    • Return top_k matches
    ↓
Ranked Results Presented to HR
```

---

## 👨‍💻 Development

### Development Setup

```bash
# Install dependencies
uv sync

# Start services
docker compose up -d db pgadmin

# Run migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload
```

### Database Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

### Code Quality

```bash
# Format code
uv run black app/

# Lint code
uv run ruff check app/

# Run all checks
uv run black app/ && uv run ruff check app/
```

### Testing

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=app tests/

# Verbose output
uv run pytest -v
```

---

## 🚀 Deployment

### Docker Production

```bash
# Build and start
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Health Checks

```bash
# Application health
curl http://localhost:8000/api/v1/health

# Docker status
docker compose ps
```

---

## 📚 Documentation

### Core Documentation

- [HYBRID_MATCHING_ARCHITECTURE.md](docs/HYBRID_MATCHING_ARCHITECTURE.md) - Matching system architecture
- [IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md) - Implementation guide
- [CV_CHAT_AGENT.md](docs/CV_CHAT_AGENT.md) - CV chat interface
- [MATCHER_AGENT.md](docs/MATCHER_AGENT.md) - Matching agent workflow
- [JOB_GENERATION_WORKFLOW.md](docs/JOB_GENERATION_WORKFLOW.md) - Job generation
- [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - Quick reference

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check if database is running
docker compose ps

# Start database
docker compose up -d db

# Test connection
docker compose exec db psql -U postgres -c "SELECT 1;"
```

#### Migration Errors

```bash
# Check current version
uv run alembic current

# Apply migrations
uv run alembic upgrade head
```

#### pgvector Extension Missing

```bash
# Enable extension
docker compose exec db psql -U postgres -d recruitment \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### OpenAI API Errors

- Verify API key in `.env` file
- Check account has credits
- Implement rate limiting

### Debug Mode

```env
DEBUG=true
LANGCHAIN_TRACING_V2=true
```

### Reset Everything

```bash
# ⚠️ WARNING: Deletes all data
docker compose down -v
docker compose up -d
uv run alembic upgrade head
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Follow code style guidelines
4. Write tests for new features
5. Submit a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **LangChain & LangGraph** - LLM orchestration
- **OpenAI** - GPT models and embeddings
- **pgvector** - Vector similarity search
- **Hackathon Team** - Development and design

---

## 📞 Contact & Support

- **Documentation**: [docs/](docs/)
- **API Docs**: http://localhost:8000/docs
- **Email**: valerio.silva@klx.pt

---

<div align="center">

**Built with ❤️ by the Hackathon Team**

**Powered by FastAPI • LangGraph • PostgreSQL • OpenAI**

⭐ Star us on GitHub if you find this useful!

</div>
