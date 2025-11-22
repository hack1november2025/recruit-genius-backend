# HR AI Recruitment Manager - Quick Start Guide

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- uv (recommended) or pip

## Setup Steps

1. **Start Docker Services**
```bash
cd local
docker compose up -d
cd ..
```

2. **Install Dependencies**
```bash
# Using uv (recommended - super fast!)
uv sync

# OR using pip
pip install -e .
```

3. **Configure Environment**
```bash
cp .env.example .env
# Edit .env and add:
# - OPENAI_API_KEY=sk-proj-your-key-here
# - DATABASE_URL (default should work with Docker setup)
```

4. **Setup Database**
```bash
# Create database in Docker container
docker exec recruitgenius-postgres psql -U recruitgenius -c "CREATE DATABASE recruitgenius;"

# Enable pgvector extension (required for embeddings)
docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations (CRITICAL - creates all required tables)
uv run alembic upgrade head

# Verify migration was successful
uv run alembic current
# Should show: effc88337b9a (head)
```

5. **Run the Server**
```bash
# Using uv
uv run uvicorn app.main:app --reload

# OR using python directly
python -m uvicorn app.main:app --reload
```

6. **Access API**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

## ⚠️ Common Issues

**Error: "relation 'cvs' does not exist"**
- You forgot to run migrations! Run: `uv run alembic upgrade head`

**Error: "could not connect to server"**
- Docker isn't running. Run: `cd local && docker compose up -d`

**Error: "extension 'vector' does not exist"**
- Enable pgvector: `docker exec recruitgenius-postgres psql -U recruitgenius recruitgenius -c "CREATE EXTENSION IF NOT EXISTS vector;"`

## Quick Test

```bash
# Create a candidate
curl -X POST http://localhost:8000/api/v1/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "skills": ["Python", "FastAPI", "AI"],
    "experience_years": "5 years",
    "resume_text": "Experienced Python developer..."
  }'

# Create a job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "description": "Looking for an experienced Python developer",
    "requirements": "5+ years of Python experience",
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "status": "open"
  }'

# Match candidate to job (AI-powered)
curl -X POST http://localhost:8000/api/v1/matches \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": 1,
    "job_id": 1
  }'
```

## Key Features Implemented

✅ Candidate Management (CRUD)
✅ Job Posting Management (CRUD)
✅ AI-Powered Resume Analysis
✅ AI-Powered Job Matching
✅ Match Scoring & Recommendations
✅ PostgreSQL with SQLAlchemy (Async)
✅ LangGraph AI Agents
✅ FastAPI with Auto-Documentation
✅ Repository Pattern
✅ Type Hints Throughout
✅ Database Migrations (Alembic)

## Project Structure

```
app/
├── agents/              # LangGraph AI agents
│   └── recruiter/       # Recruitment workflow
├── api/                 # FastAPI routes
│   └── routes/          # Endpoint definitions
├── core/                # Configuration
├── db/                  # Database setup
│   └── models/          # SQLAlchemy models
├── repositories/        # Data access layer
├── schemas/             # Pydantic schemas
├── services/            # Business logic
└── main.py             # Application entry
```

## For Hackathon

This is a minimal, functional implementation following KISS and DRY principles. It's ready to extend with:

- Authentication/Authorization
- More sophisticated AI agents
- Interview scheduling
- Email notifications
- Advanced analytics
- Resume parsing from files
- Integration with job boards

Good luck with your hackathon! 🚀
