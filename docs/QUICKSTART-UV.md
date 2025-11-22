# 🚀 Quick Start with uv

## One-Time Setup

```bash
# 1. Install dependencies (creates .venv automatically)
uv sync

# 2. Setup environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Setup database
createdb recruitgenius
uv run alembic upgrade head
```

## Daily Development

```bash
# Start the server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest

# Format code
uv run black app/
uv run ruff check app/
```

## Adding Dependencies

```bash
# Add a regular dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name
```

## That's it! 🎉

The project is now using **uv** - it's 10-100x faster than pip/poetry!
Visit http://localhost:8000/docs once the server is running.
