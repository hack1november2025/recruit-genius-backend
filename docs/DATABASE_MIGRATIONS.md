# Database Migrations Guide

## Overview

This project uses Alembic for database schema migrations. All migration files are now tracked in Git to ensure database consistency across all environments.

## Migration Files Location

- **Path:** `alembic/versions/`
- **Status:** ✅ **Now tracked in Git** (previously ignored - FIXED!)
- **Current migrations:**
  - `001_initial_schema.py` - Baseline schema with all core tables

## For New Team Members / Fresh Database Setup

### 1. Initial Setup

```bash
# Install dependencies
uv sync  # or poetry install

# Ensure PostgreSQL is running (via Docker)
docker-compose up -d postgres

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/recruitment"
```

### 2. Run Migrations

```bash
# Apply all migrations
alembic upgrade head

# Verify current version
alembic current -v
```

This will create all necessary tables:
- `candidates` - Candidate profiles
- `jobs` - Job postings  
- `matches` - AI-powered candidate-job matches
- `cvs` - Multiple CVs per candidate
- `cv_metrics` - Structured CV evaluation scores
- `job_metadata` - Extracted job requirements
- `langchain_pg_collection` - LangChain RAG collections
- `langchain_pg_embedding` - Vector embeddings for semantic search

## For Existing Databases (Migration from Untracked State)

If you already have a database with tables created but no migration history:

```bash
# Stamp the database with the baseline migration
alembic stamp head

# Verify it worked
alembic current -v
```

## Creating New Migrations

### 1. Auto-generate migration (recommended)

```bash
# Make changes to your SQLAlchemy models in app/db/models/
# Then generate migration
alembic revision --autogenerate -m "description_of_changes"

# Review the generated file in alembic/versions/
# Make any necessary adjustments

# Apply the migration
alembic upgrade head
```

### 2. Manual migration (for complex changes)

```bash
# Create empty migration file
alembic revision -m "description_of_changes"

# Edit the generated file and add your upgrade/downgrade logic
# Then apply it
alembic upgrade head
```

## Common Migration Commands

```bash
# Show current migration version
alembic current

# Show migration history
alembic history -v

# Upgrade to latest
alembic upgrade head

# Upgrade by 1 version
alembic upgrade +1

# Downgrade by 1 version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>

# Downgrade to base (empty database)
alembic downgrade base
```

## Migration Best Practices

### 1. Always Review Auto-generated Migrations

Auto-generate is helpful but not perfect. Always review and test:

```bash
alembic revision --autogenerate -m "add_column"
# Review alembic/versions/<new_file>.py
# Test in development before committing
```

### 2. Test Migrations Both Ways

```bash
# Test upgrade
alembic upgrade head

# Test downgrade (data may be lost!)
alembic downgrade -1

# Re-upgrade
alembic upgrade head
```

### 3. Avoid Breaking Changes

When modifying existing columns:

```python
# ❌ BAD - Drops data
op.drop_column('candidates', 'old_field')

# ✅ GOOD - Multi-step migration
# Migration 1: Add new field
op.add_column('candidates', sa.Column('new_field', sa.String(), nullable=True))

# Migration 2: Migrate data (if needed)
# Manual SQL or Python script

# Migration 3: Drop old field
op.drop_column('candidates', 'old_field')
```

### 4. Use Transactions

Alembic uses PostgreSQL transactions by default. If a migration fails, changes are rolled back.

For data migrations, consider:

```python
def upgrade():
    # Get database connection
    conn = op.get_bind()
    
    # Execute data migration
    conn.execute(sa.text("""
        UPDATE candidates 
        SET status = 'new' 
        WHERE status IS NULL
    """))
```

## Troubleshooting

### "Can't locate revision identified by X"

This means the `alembic_version` table references a migration file that doesn't exist.

**Fix:**

```bash
# Clear the broken reference
python -c "
from app.db.session import engine
from sqlalchemy import text
import asyncio

async def fix():
    async with engine.begin() as conn:
        await conn.execute(text('DELETE FROM alembic_version'))
        
asyncio.run(fix())
"

# Stamp with current migration
alembic stamp head
```

### "Target database is not up to date"

Run migrations:

```bash
alembic upgrade head
```

### "FAILED: Multiple head revisions are present"

You have branching migration history. Merge them:

```bash
alembic merge heads -m "merge_branches"
alembic upgrade head
```

### Checking Database Schema vs Models

```bash
# Generate a migration to see what's different
alembic revision --autogenerate -m "check_differences"

# Review the generated file
# If it's empty, schema matches models
# If not, review the changes

# You can delete it if you don't want the changes
rm alembic/versions/<generated_file>.py
```

## Database Schema Alignment Check

To verify the database schema matches the SQLAlchemy models:

```python
# This script compares database schema with models
from alembic.autogenerate import compare_metadata
from app.db.base import Base
from app.db.session import engine
from alembic.migration import MigrationContext
import asyncio

async def check_schema():
    async with engine.connect() as conn:
        def check(connection):
            context = MigrationContext.configure(connection)
            diff = compare_metadata(context, Base.metadata)
            
            if not diff:
                print("✅ Database schema matches models!")
            else:
                print("⚠️  Database schema differs from models:")
                for item in diff:
                    print(f"  - {item}")
        
        await conn.run_sync(check)

asyncio.run(check_schema())
```

## Environment-Specific Notes

### Development

- Migrations auto-apply on container restart (if `alembic upgrade head` is in entrypoint)
- Safe to reset database: `alembic downgrade base && alembic upgrade head`

### Production

- **Never** auto-run migrations in production
- Test migrations in staging first
- Back up database before migrating
- Have a rollback plan (test downgrades in staging)

### CI/CD

Add migration check to CI:

```bash
# Check if migrations are up to date
alembic check  # (Alembic 1.7+)

# Or generate a migration and check if it's empty
alembic revision --autogenerate -m "ci_check"
# If file is not empty, fail the build
```

## Migration Strategy

### Current State (After Cleanup)

1. ✅ `.gitignore` fixed - migrations are now tracked
2. ✅ Broken migrations removed
3. ✅ Clean baseline migration created (`001_initial`)
4. ✅ Database stamped with baseline
5. ✅ Migration chain verified

### Going Forward

1. **All migrations are tracked in Git** - no more ignored files!
2. **Baseline migration** covers all current tables
3. **New changes** go in new migration files
4. **Team members** can clone and run `alembic upgrade head` to set up their database

## Common Issues Fixed

### ❌ Old Problem: Migrations Not Tracked

```gitignore
# OLD .gitignore (WRONG)
alembic/versions/*.py
!alembic/versions/.gitkeep
```

**Result:** Other developers couldn't run migrations!

### ✅ New Solution: Migrations Tracked

```gitignore
# NEW .gitignore (CORRECT)
# Only ignore backup files
alembic/versions/*.bak
alembic/versions/*~
```

**Result:** Everyone can run migrations! 🎉

## Quick Start Commands

```bash
# Clone the repo
git clone <repo_url>
cd backend

# Setup environment
uv sync
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Verify
alembic current -v
```

That's it! Your database is now ready to use.
