# Infrastructure Cleanup Summary

## Overview
Removed unused infrastructure from the project to reduce complexity and improve maintainability.

## Changes Made

### 1. ✅ Removed Redis Infrastructure
**Reason**: Redis was configured but never used in the application code.

**Files Modified:**
- `docker-compose.yml` - Removed Redis service and dependency
- `app/core/config.py` - Removed `redis_url` configuration
- `.env` and `.env.example` - Removed `REDIS_URL` environment variable
- `pyproject.toml` - Removed `redis>=5.0.0` dependency

**Note**: Langfuse still requires Redis internally and manages its own Redis connection.

---

### 2. ✅ Removed `agent_executions` Table
**Reason**: Table was never used in the application. LangGraph's built-in checkpointer system handles agent execution tracking.

**Migration**: `6b6c9713cb1a_drop_unused_agent_executions_table.py`

**Changes:**
- Dropped `agent_executions` table from database
- Dropped PostgreSQL enum types: `agenttype`, `executionstatus`
- Deleted `app/db/models/agent_execution.py` model file
- Removed imports from `app/db/models/__init__.py`

**Database Before:**
```
16 tables including agent_executions
```

**Database After:**
```
15 tables (agent_executions removed)
```

---

### 3. ✅ Removed Unused Embedding Models
**Reason**: These models were already replaced by LangChain's native vector store schema in previous migrations.

**Tables Already Dropped** (by migration `e34c136a9313`):
- `cv_embeddings` → Replaced by `langchain_pg_embedding`
- `job_embeddings` → Replaced by `langchain_pg_embedding`

**Code Cleanup:**
- Deleted `app/db/models/cv_embedding.py`
- Deleted `app/db/models/job_embedding.py`
- Removed unused import from `app/agents/matcher/nodes.py`
- Removed exports from `app/db/models/__init__.py`

---

### 4. ✅ Removed `chat_sessions` and `chat_messages` Tables
**Reason**: Tables were replaced by LangGraph's built-in checkpointer system which handles all conversation state and history automatically per `thread_id`.

**Migration**: `7b8facf0958d_drop_unused_chat_tables.py`

**Changes:**
- Dropped `chat_sessions` table from database
- Dropped `chat_messages` table from database
- Deleted `app/db/models/chat_session.py` model file
- Deleted `app/db/models/chat_message.py` model file
- Deleted `app/repositories/chat_session.py` repository file
- Deleted `app/repositories/chat_message.py` repository file
- Removed imports from `app/db/models/__init__.py`

**Database Before:**
```
15 tables including chat_sessions and chat_messages
```

**Database After:**
```
13 tables (chat tables removed)
```

---

## Current Database Schema

### Active Tables (13):
1. `alembic_version` - Migration tracking
2. `candidates` - Candidate profiles
3. `checkpoint_blobs` - LangGraph checkpointer blobs
4. `checkpoint_migrations` - LangGraph checkpointer migrations
5. `checkpoint_writes` - LangGraph checkpointer writes
6. `checkpoints` - LangGraph conversation state (replaces chat_sessions/chat_messages)
7. `cv_metrics` - CV matching metrics
8. `cvs` - CV/Resume data
9. `job_metadata` - Extracted job metadata
10. `jobs` - Job postings
11. `langchain_pg_collection` - Vector store collections
12. `langchain_pg_embedding` - Vector embeddings for CVs and jobs
13. `matches` - Job-candidate matches

---

## Benefits

1. **Reduced Complexity**: Removed 7 unused model/repository files and 3 unused tables
2. **Clearer Architecture**: Only active infrastructure remains
3. **Easier Maintenance**: Less code to maintain and understand
4. **Resource Optimization**: Removed Redis container (not needed)
5. **Simplified Conversation Management**: Single source of truth via LangGraph checkpointer

---

## Migration Order

The cleanup migrations should be run in this order:

1. `e34c136a9313` - Drop old cv_embeddings and job_embeddings tables
2. `6b6c9713cb1a` - Drop agent_executions table
3. `7b8facf0958d` - Drop chat_sessions and chat_messages tables

All migrations have been successfully applied to the database.

---

## Next Steps

If you need to track agent executions in the future, use LangGraph's built-in checkpointer instead of creating a custom table. The checkpointer provides:

- Automatic conversation history
- State persistence
- Thread-based isolation
- Built-in checkpoint management

