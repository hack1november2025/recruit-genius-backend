# LLM Model Configuration

## Overview

The application now uses centralized LLM model configuration via environment variables, making it easy to switch between different OpenAI models (e.g., gpt-4o, gpt-4o-mini, gpt-4-turbo) without code changes.

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# LLM Models
LLM_MODEL=gpt-4o              # Model for general agents
LLM_RAG_MODEL=gpt-4o          # Model for RAG/chat agents
```

### Defaults

If not specified, both default to `gpt-4o`:
- `LLM_MODEL`: Default is `gpt-4o`
- `LLM_RAG_MODEL`: Default is `gpt-4o`

## Model Usage by Component

### General Agents (`LLM_MODEL`)
- **Job Generator** - Job description creation and refinement
- **Recruiter Agent** - Resume analysis, matching, recommendations
- **Metadata Extraction** - CV and job metadata extraction
- **Translation Service** - Text translation
- **Job Metadata Extraction** - Structured job data extraction

### RAG/Chat Agents (`LLM_RAG_MODEL`)
- **CV Chat Agent** - Conversational candidate search with RAG
- **Query Understanding** - Intent detection and parameter extraction
- **Summarization** - Context summarization in RAG

## Switching Models

### Example: Use gpt-4o-mini for cost savings

```env
LLM_MODEL=gpt-4o-mini
LLM_RAG_MODEL=gpt-4o-mini
```

### Example: Use gpt-4o for better quality

```env
LLM_MODEL=gpt-4o
LLM_RAG_MODEL=gpt-4o
```

### Example: Hybrid approach

```env
LLM_MODEL=gpt-4o-mini         # Cheaper for general tasks
LLM_RAG_MODEL=gpt-4o          # Better for RAG/search
```

## Docker Deployment

The `docker-compose.yml` is configured to use these environment variables:

```yaml
environment:
  LLM_MODEL: ${LLM_MODEL:-gpt-4o}
  LLM_RAG_MODEL: ${LLM_RAG_MODEL:-gpt-4o}
```

Just set them in your `.env` file before running:

```bash
docker compose up --build
```

## Testing

Verify your configuration:

```bash
uv run python test_model_config.py
```

## Implementation Details

All LLM instantiations now use:

```python
from app.core.config import get_settings

settings = get_settings()

# For general agents
llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=0.7,
    openai_api_key=settings.openai_api_key
)

# For RAG agents
llm = ChatOpenAI(
    model=settings.llm_rag_model,
    temperature=0,
    openai_api_key=settings.openai_api_key
)
```

## Files Modified

1. `app/core/config.py` - Added `llm_model` and `llm_rag_model` settings
2. `app/agents/job_generator/nodes.py` - Uses `settings.llm_model`
3. `app/agents/cv_chat/nodes.py` - Uses `settings.llm_rag_model`
4. `app/agents/cv_chat/graph.py` - Uses `settings.llm_rag_model`
5. `app/agents/recruiter/nodes.py` - Uses `settings.llm_model`
6. `app/services/job_metadata_extraction_service.py` - Uses `settings.llm_model`
7. `app/services/translation_service.py` - Uses `settings.llm_model`
8. `app/services/metadata_extraction_service.py` - Uses `settings.llm_model`
9. `.env` - Added model configuration
10. `docker-compose.yml` - Added environment variables

## Benefits

✅ **Centralized Configuration** - Change models in one place  
✅ **Environment-Specific** - Different models per environment  
✅ **Cost Optimization** - Easy to switch to cheaper models  
✅ **Quality Tuning** - Use better models for critical features  
✅ **Docker Compatible** - Works seamlessly in containers  
✅ **No Code Changes** - Modify behavior via environment variables
