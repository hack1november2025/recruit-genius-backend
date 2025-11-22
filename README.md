# HR AI Recruitment Manager - Backend

AI-powered recruitment assistant built with FastAPI, LangGraph, and PostgreSQL.

## Features

- **🤖 Conversational Job Generator**: AI-powered job description creation with context maintenance
- **📄 Resume Analysis**: Parse and analyze candidate resumes (PDF/DOCX)
- **🎯 Job Matching**: Match candidates to job positions using AI with 8-metric evaluation
- **💬 RAG Chat Interface**: Semantic search across CVs with pgvector
- **📊 Analytics Dashboard**: Real-time recruitment metrics and insights
- **🐳 Docker Ready**: One-command deployment with automated migrations

## Tech Stack

- **FastAPI**: Modern async web framework
- **LangGraph 0.2.45**: AI agent orchestration with PostgreSQL checkpointing
- **LangChain 0.3.7**: LLM integration and tools
- **PostgreSQL + pgvector**: Database with vector similarity search
- **Redis**: Caching layer for analytics
- **OpenAI**: GPT-4o-mini for generation, text-embedding-3-small for embeddings
- **Docker & Docker Compose**: Containerized deployment

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API Key

### Option 1: Docker (Recommended)

The fastest way to get started is using Docker with the automated setup script:

```bash
# 1. Copy environment file and add your OpenAI API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=your-key-here

# 2. Run the automated Docker setup script
./docker-start.sh
```

That's it! The script will:
- Build the Docker image with all dependencies
- Start PostgreSQL (with pgvector), Redis, and the application
- Automatically run all database migrations
- Verify the application is healthy

**Access the application:**
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

**Docker commands:**
```bash
# View logs
docker compose logs -f app

# Stop services
docker compose down

# Restart
docker compose restart app

# Rebuild after code changes
docker compose up -d --build
```

See [README.Docker.md](README.Docker.md) for detailed Docker documentation.

---

### Option 2: Local Development (with uv)

For local development with hot-reload:

**Prerequisites:**
- uv (Python package manager)

Install uv if you haven't:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation

1. **Clone and enter the directory:**
```bash
cd backend
```

2. **Start Docker services:**
```bash
cd local
docker compose up -d
cd ..
```

This starts PostgreSQL on `localhost:5432` and pgAdmin on `localhost:5050`.

3. **Install Python dependencies:**
```bash
uv sync
```

4. **Set up environment:**
```bash
cp .env.example .env
```

Edit `.env` and configure the following **required** settings:
```env
# REQUIRED: Add your OpenAI API key
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Database connection (update if using different credentials)
DATABASE_URL=postgresql+asyncpg://recruitgenius:recruitgenius_dev@localhost:5432/recruitgenius
```

5. **Create database and enable pgvector extension:**
```bash
# Create database in Docker container
docker exec recruitgenius-postgres psql -U recruitgenius -c "CREATE DATABASE recruitgenius;"

# Enable pgvector extension (required for embeddings)
docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

6. **Run database migrations:**

**⚠️ IMPORTANT:** This project uses Alembic migrations. You **MUST** run all migrations to create the required database schema. The migrations create:
- Base tables (candidates, jobs, matches, agent_executions)
- CV processing tables (cvs, cv_embeddings, cv_metrics)
- Job metadata tables (job_embeddings, job_metadata)
- Chat session tables (chat_sessions, chat_messages)

```bash
# Apply all migrations to create database schema
uv run alembic upgrade head
```

**Verify migrations were applied:**
```bash
# Check migration history
uv run alembic current

# Should show: effc88337b9a (head)
```

**If you see errors about missing tables or columns**, it means migrations weren't run. Always run `uv run alembic upgrade head` after pulling changes.

7. **Start the server:**
```bash
uv run uvicorn app.main:app --reload
```

8. **Access the API:**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health
- pgAdmin: http://localhost:5050 (admin@recruitgenius.com / admin)

## Project Structure

```
app/
├── agents/              # LangGraph agents
│   └── recruiter/       # Main recruitment agent
├── api/                 # API routes
├── core/                # Configuration
├── db/                  # Database models
├── repositories/        # Data access layer
├── schemas/             # Pydantic schemas
├── services/            # Business logic
└── main.py             # Entry point
```

## API Endpoints

### Conversational Job Generator (NEW)
- `POST /api/v1/job-descriptions/chat` - Chat with job generator agent
  - Send simple text: `{"message": "Create job for senior Python developer"}`
  - Returns markdown job description with thread_id
  - Use thread_id to continue conversation: `?thread_id=job_abc123`
  - Request modifications: `{"message": "Make it more friendly"}`
  - Save to database: `{"message": "Save with title Senior Python Developer"}`
- `POST /api/v1/job-descriptions/chat/stream` - Streaming version

### Standard CRUD
- `POST /api/v1/candidates` - Create candidate
- `POST /api/v1/candidates/{id}/analyze` - Analyze resume
- `POST /api/v1/jobs` - Create job posting
- `POST /api/v1/matches` - Match candidates to jobs
- `GET /api/v1/candidates` - List candidates
- `GET /api/v1/jobs` - List jobs

### Quick Test
```bash
# Test conversational job generator
./test_chat_api.sh

# Or manually
curl -X POST "http://localhost:8000/api/v1/job-descriptions/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Create job for senior backend engineer with Python"}'
```

## Development

### Database Schema Version

**Current Migration:** `effc88337b9a` (November 21, 2025)

This migration includes:
- ✅ CV processing with separate `cvs` table
- ✅ CV embeddings (pgvector) linked to `cvs`
- ✅ Job embeddings for semantic job matching
- ✅ Job metadata extraction and storage
- ✅ 8-metric CV evaluation system
- ✅ Chat session management

**If you're not on this version, run:** `uv run alembic upgrade head`

### Running Tests
```bash
uv run pytest
```

### Code Formatting
```bash
uv run black app/
uv run ruff check app/
```

### Database Management

#### View Database Schema

```bash
# View database tables
docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "\dt"

# Access database shell
docker exec -it recruitgenius-postgres psql -U recruitgenius recruitgenius

# View specific table structure
docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "\d candidates"
```

#### Migration Management

This project uses **Alembic** for database migrations. The migration history is:

1. **d96d37f98471** - Initial schema (candidates, jobs, matches, agent_executions)
2. **4165a975d65b** - Add cv_embeddings, cv_metrics, chat_sessions tables
3. **effc88337b9a** (HEAD) - Add cvs, job_embeddings, job_metadata, refactor relations

```bash
# Create new migration (after model changes)
uv run alembic revision --autogenerate -m "description of changes"

# Apply migrations (upgrade to latest)
uv run alembic upgrade head

# Apply specific migration
uv run alembic upgrade <revision_id>

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history

# View current migration version
uv run alembic current
```

**⚠️ Always run migrations after pulling new code!**

### Docker Commands
```bash
# Start services
cd local && docker compose up -d

# Stop services
cd local && docker compose down

# View logs
docker compose logs -f postgres

# Restart services
cd local && docker compose restart
```

## Troubleshooting

### Common Issues on New Machines

**❌ Error: "relation [table_name] does not exist" or "column [column_name] does not exist"**

This means database migrations haven't been applied. **Solution:**
```bash
# Ensure database exists
docker exec recruitgenius-postgres psql -U recruitgenius -c "CREATE DATABASE recruitgenius;"

# Enable pgvector extension
docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Apply ALL migrations
uv run alembic upgrade head

# Verify current migration version
uv run alembic current
# Should show: effc88337b9a (head)
```

**❌ Error: "could not connect to server"**

Database container isn't running. **Solution:**
```bash
# Check if containers are running
cd local && docker compose ps

# Start containers if stopped
docker compose up -d

# Check logs for errors
docker compose logs postgres
```

**❌ Error: "No module named 'pgvector'" or "extension 'vector' does not exist"**

The pgvector extension isn't enabled. **Solution:**
```bash
# Connect to database and enable extension
docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**❌ Error: "openai.AuthenticationError" or "Invalid API key"**

Missing or invalid OpenAI API key. **Solution:**
```bash
# Edit .env file and add valid key
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Restart the server after updating .env
```

### Database Issues

**Check database connection:**
```bash
# Test database connection
docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "SELECT version();"

# List all tables
docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "\dt"

# Expected tables:
# - candidates, jobs, matches, agent_executions
# - cvs, cv_embeddings, cv_metrics
# - job_embeddings, job_metadata
# - chat_sessions, chat_messages
```

**Reset database (⚠️ deletes all data):**
```bash
# Drop and recreate database
docker exec recruitgenius-postgres psql -U recruitgenius -c "DROP DATABASE IF EXISTS recruitgenius;"
docker exec recruitgenius-postgres psql -U recruitgenius -c "CREATE DATABASE recruitgenius;"

# Enable pgvector
docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations from scratch
uv run alembic upgrade head
```

**Check migration history:**
```bash
# View applied migrations
uv run alembic history

# View current migration
uv run alembic current

# Should be at: effc88337b9a (head)
```

### Port Conflicts

**Port already in use (5432, 8000, 5050):**
```bash
# Check what's using the ports
lsof -i :5432  # PostgreSQL
lsof -i :8000  # FastAPI
lsof -i :5050  # pgAdmin

# Option 1: Stop conflicting service
sudo systemctl stop postgresql  # if system PostgreSQL is running

# Option 2: Change ports in docker-compose.yaml and .env
```

### Environment Setup

**Verify environment configuration:**
```bash
# Check if .env file exists
ls -la .env

# View current environment variables (without secrets)
grep -v "API_KEY" .env

# Required variables:
# - DATABASE_URL
# - OPENAI_API_KEY
# - REDIS_URL (optional, for caching)
```

### Starting Fresh on a New Computer

Complete setup from scratch:
```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone repo and enter directory
cd backend

# 3. Start Docker services
cd local && docker compose up -d && cd ..

# 4. Install dependencies
uv sync

# 5. Create .env file
cp .env.example .env
# Edit .env and add OPENAI_API_KEY

# 6. Create database
docker exec recruitgenius-postgres psql -U recruitgenius -c "CREATE DATABASE recruitgenius;"

# 7. Enable pgvector
docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 8. Run migrations
uv run alembic upgrade head

# 9. Verify setup
uv run alembic current  # Should show: effc88337b9a
docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "\dt"  # Should list all tables

# 10. Start server
uv run uvicorn app.main:app --reload
```

### Quick Diagnostics

Run these commands to diagnose issues:

```bash
# Check Docker containers status
cd local && docker compose ps

# Check database connection
docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "SELECT 1;"

# Check installed tables
docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "\dt"

# Check migration version
uv run alembic current

# Check Python environment
uv run python --version
which python

# Test OpenAI connection
uv run python -c "import openai; print('OpenAI module loaded')"
```

## Additional Resources

- **Documentation**: See `docs/` folder for detailed architecture and implementation guides
- **API Documentation**: http://localhost:8000/docs (when server is running)
- **pgAdmin**: http://localhost:5050 for database management
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **FastAPI Docs**: https://fastapi.tiangolo.com/

## License

MIT
