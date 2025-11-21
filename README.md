# HR AI Recruitment Manager - Backend

AI-powered recruitment assistant built with FastAPI, LangGraph, and PostgreSQL.

## Features

- **Resume Analysis**: Parse and analyze candidate resumes
- **Job Matching**: Match candidates to job positions using AI
- **Interview Scheduling**: Manage interview scheduling and coordination
- **Candidate Screening**: AI-powered initial screening conversations

## Tech Stack

- **FastAPI**: Modern async web framework
- **LangGraph**: AI agent orchestration with state management
- **PostgreSQL**: Database with LangGraph checkpointing
- **OpenAI**: LLM for intelligent processing

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- uv (for Python package management)

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

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

5. **Create database and run migrations:**
```bash
# Create database in Docker container
docker exec speaksy-postgres psql -U speaksy -c "CREATE DATABASE hr_recruitment;"

# Run migrations
uv run alembic upgrade head
```

6. **Start the server:**
```bash
uv run uvicorn app.main:app --reload
```

7. **Access the API:**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health
- pgAdmin: http://localhost:5050 (admin@speaksy.com / admin)

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

- `POST /api/v1/candidates` - Create candidate
- `POST /api/v1/candidates/{id}/analyze` - Analyze resume
- `POST /api/v1/jobs` - Create job posting
- `POST /api/v1/matches` - Match candidates to jobs
- `GET /api/v1/candidates` - List candidates
- `GET /api/v1/jobs` - List jobs

## Development

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
```bash
# View database tables
docker exec speaksy-postgres psql -U speaksy hr_recruitment -c "\dt"

# Access database shell
docker exec -it speaksy-postgres psql -U speaksy hr_recruitment

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

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

**Database connection error:**
- Ensure Docker containers are running: `docker compose ps`
- Check `.env` has correct DATABASE_URL: `postgresql+asyncpg://speaksy:speaksy_dev@localhost:5432/hr_recruitment`

**Missing OpenAI API key:**
- Add your key to `.env`: `OPENAI_API_KEY=sk-proj-...`

**Port already in use:**
- Stop other services using port 5432 or 8000
- Or modify ports in `local/docker-compose.yaml` and `.env`

## License

MIT
