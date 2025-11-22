# CV Database Chat Agent - Architecture & Usage Guide

## Overview

The CV Database Chat Agent is a conversational AI interface that enables HR personnel to query, filter, and extract insights from the CV vector database using natural language. Built with LangGraph 1.0 and FastAPI, it provides both web UI and Telegram bot integration.

## Architecture

### Components

```
app/
├── agents/cv_chat/              # LangGraph CV Chat Agent
│   ├── state.py                 # Agent state schema with conversation context
│   ├── tools.py                 # RAG retrieval and candidate search tools
│   ├── nodes.py                 # Query understanding, retrieval, response generation
│   └── graph.py                 # LangGraph workflow orchestration
├── services/
│   └── chat_orchestrator.py    # Session management and workflow coordination
├── repositories/
│   ├── chat_session.py          # Chat session persistence
│   └── chat_message.py          # Message history management
├── api/routes/
│   └── chat.py                  # REST API endpoints
├── db/models/
│   ├── chat_session.py          # Chat session model
│   └── chat_message.py          # Chat message model
└── schemas/
    └── chat.py                  # Pydantic schemas for requests/responses
```

### Agent Workflow

The CV Chat agent follows a 3-node LangGraph workflow:

1. **understand_query**: Analyzes user query using LLM to extract intent and search parameters
   - Intent types: `search`, `filter`, `compare`, `detail`, `clarify`
   - Extracts structured parameters: skills, experience, location, companies, etc.
   - Determines if clarification is needed

2. **retrieve_candidates**: Executes appropriate retrieval strategy based on intent
   - `search`: Performs RAG vector similarity search
   - `filter`: Applies filters to existing candidates in context
   - `compare`: Gets detailed info for multiple candidates
   - `detail`: Retrieves full profile for one candidate

3. **generate_response**: Creates natural language response with structured data
   - Uses conversation history for context
   - Generates user-friendly text response
   - Creates structured JSON for UI rendering
   - Updates conversation messages

### State Management

The agent maintains conversational state using `CVChatState`:

```python
class CVChatState(TypedDict):
    # Conversation context
    messages: list[BaseMessage]           # Full conversation history
    session_id: int                       # Database session ID
    user_identifier: str                  # User ID (web/telegram)
    
    # Current query
    user_query: str                       # Latest query text
    query_intent: str                     # Detected intent
    search_params: Dict[str, Any]         # Extracted parameters
    
    # Results
    candidate_results: List[Dict]         # Retrieved candidates
    candidate_ids_in_context: List[int]   # IDs for follow-up queries
    
    # Response
    response_text: str                    # Natural language response
    structured_response: Dict             # JSON for UI rendering
```

## Key Features

### Natural Language Querying

Users can ask questions in plain English:

```
"Find me senior Python developers in London with over 5 years of experience"
"Who among them has AWS experience?"
"Compare the top 3 candidates"
"What are John Doe's programming languages?"
```

### Multi-Turn Conversations

The agent maintains context across multiple turns:

```
User: "Show me software engineers"
Agent: [Returns 10 candidates]

User: "Among them, who has AWS experience?"
Agent: [Filters previous results for AWS]

User: "Compare the top 3"
Agent: [Provides detailed comparison]
```

### RAG-Based Search

- Uses vector embeddings for semantic similarity
- Searches across all CV text and metadata
- Configurable similarity thresholds
- Returns ranked candidates with scores

### Rich Candidate Information

For each candidate, the agent can provide:
- Skills and technologies
- Years of experience
- Education history
- Job titles and companies
- Location
- Certifications and languages
- Full CV text

## API Endpoints

### Create Chat Session

```http
POST /api/v1/chat/sessions
Content-Type: application/json

{
  "session_name": "Software Engineers Search"
}

Response: 201 Created
{
  "id": 1,
  "session_name": "Software Engineers Search",
  "created_at": "2025-11-22T10:00:00Z",
  "updated_at": "2025-11-22T10:00:00Z",
  "message_count": 0
}
```

### Process Chat Query

```http
POST /api/v1/chat/query
Content-Type: application/json

{
  "query": "Find me senior Python developers in London",
  "session_id": 1,  # Optional - creates new session if omitted
  "user_identifier": "web_user"
}

Response: 200 OK
{
  "session_id": 1,
  "response_text": "I found 5 senior Python developers in London...",
  "structured_response": {
    "type": "candidates",
    "message": "I found 5 senior Python developers...",
    "candidates": [
      {
        "candidate_id": 42,
        "name": "John Doe",
        "email": "john@example.com",
        "skills": ["Python", "Django", "PostgreSQL"],
        "experience_years": 7,
        "location": "London, UK",
        "similarity_score": 0.87,
        "summary": "Experienced Python developer..."
      }
    ],
    "total_count": 5
  },
  "candidate_ids": [42, 43, 44, 45, 46],
  "error": null
}
```

### Get Chat History

```http
GET /api/v1/chat/sessions/1

Response: 200 OK
{
  "session": {
    "id": 1,
    "session_name": "Software Engineers Search",
    "created_at": "2025-11-22T10:00:00Z",
    "updated_at": "2025-11-22T10:15:00Z",
    "message_count": 6
  },
  "messages": [
    {
      "id": 1,
      "session_id": 1,
      "role": "user",
      "content": "Find me senior Python developers",
      "candidate_ids": [],
      "message_metadata": {},
      "created_at": "2025-11-22T10:00:00Z"
    },
    {
      "id": 2,
      "session_id": 1,
      "role": "assistant",
      "content": "I found 5 senior Python developers...",
      "candidate_ids": [42, 43, 44, 45, 46],
      "message_metadata": {...},
      "created_at": "2025-11-22T10:00:05Z"
    }
  ]
}
```

### List Chat Sessions

```http
GET /api/v1/chat/sessions?limit=20

Response: 200 OK
[
  {
    "id": 1,
    "session_name": "Software Engineers Search",
    "created_at": "2025-11-22T10:00:00Z",
    "updated_at": "2025-11-22T10:15:00Z",
    "message_count": 6
  }
]
```

### Delete Chat Session

```http
DELETE /api/v1/chat/sessions/1

Response: 204 No Content
```

### Telegram Bot Integration

```http
POST /api/v1/chat/telegram
Content-Type: application/json

{
  "telegram_user_id": "123456789",
  "message": "Find Python developers in London",
  "session_id": null  # Optional - maintains per-user sessions
}

Response: 200 OK
{
  "session_id": 2,
  "response_text": "I found 5 senior Python developers...",
  "candidates": [
    {
      "candidate_id": 42,
      "name": "John Doe",
      "email": "john@example.com",
      "skills": ["Python", "Django", "PostgreSQL"],
      "experience_years": 7,
      "location": "London, UK",
      "similarity_score": 0.87,
      "summary": "Experienced Python developer..."
    }
  ]
}
```

## Usage Examples

### Web UI Integration

```javascript
// Create a new chat session
const session = await fetch('/api/v1/chat/sessions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_name: 'New Search' })
}).then(r => r.json());

// Send a query
const response = await fetch('/api/v1/chat/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Find senior Python developers',
    session_id: session.id,
    user_identifier: 'web_user'
  })
}).then(r => r.json());

// Display response
console.log(response.response_text);
console.log(response.structured_response.candidates);

// Follow-up query (maintains context)
const followUp = await fetch('/api/v1/chat/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Who among them has AWS experience?',
    session_id: session.id,
    user_identifier: 'web_user'
  })
}).then(r => r.json());
```

### Python Client Example

```python
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def chat_example():
    async with httpx.AsyncClient() as client:
        # Create session
        session = await client.post(
            f"{BASE_URL}/chat/sessions",
            json={"session_name": "Python Developers"}
        )
        session_data = session.json()
        session_id = session_data["id"]
        
        # Send query
        response = await client.post(
            f"{BASE_URL}/chat/query",
            json={
                "query": "Find senior Python developers in London",
                "session_id": session_id,
                "user_identifier": "python_client"
            }
        )
        result = response.json()
        
        print(result["response_text"])
        print(f"Found {len(result['candidate_ids'])} candidates")
        
        # Follow-up query
        response2 = await client.post(
            f"{BASE_URL}/chat/query",
            json={
                "query": "Show me the top 3",
                "session_id": session_id,
                "user_identifier": "python_client"
            }
        )
        result2 = response2.json()
        
        for candidate in result2["structured_response"]["candidates"]:
            print(f"{candidate['name']}: {', '.join(candidate['skills'][:5])}")
```

## Query Intent Types

The agent automatically detects query intent:

### Search Intent
- **Trigger**: New search queries, broad questions
- **Examples**: 
  - "Find Python developers"
  - "Show me candidates with AWS experience"
  - "Who has a PhD in Computer Science?"
- **Action**: Performs RAG vector search across all CVs

### Filter Intent
- **Trigger**: Refinement of previous results
- **Examples**:
  - "Among them, who has AWS?"
  - "Filter by London location"
  - "Show only those with 5+ years experience"
- **Action**: Applies filters to candidates already in context

### Compare Intent
- **Trigger**: Comparison requests
- **Examples**:
  - "Compare the top 3 candidates"
  - "Show me differences between John and Jane"
- **Action**: Retrieves detailed profiles for side-by-side comparison

### Detail Intent
- **Trigger**: Questions about specific candidate
- **Examples**:
  - "What are John Doe's programming languages?"
  - "Tell me more about the first candidate"
- **Action**: Returns comprehensive profile information

### Clarify Intent
- **Trigger**: Ambiguous or unclear queries
- **Examples**:
  - "Show me some people"
  - "Find good candidates"
- **Action**: Asks user for more specific criteria

## Search Parameters

The agent can extract and use these parameters:

- `skills`: List of required/preferred skills
- `min_experience_years`: Minimum years of experience
- `location`: Geographic location
- `companies`: Previous employers
- `job_titles`: Desired job titles/roles
- `education`: Education level or degrees

## Database Schema

### chat_sessions Table

```sql
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    session_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### chat_messages Table

```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    candidate_ids INTEGER[],
    message_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Configuration

Required environment variables:

```bash
# OpenAI for LLM and embeddings
OPENAI_API_KEY=sk-...

# Optional: LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=cv-chat-agent

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
```

## Error Handling

The agent handles various error scenarios:

1. **No candidates found**: Suggests alternative search criteria
2. **Ambiguous query**: Asks clarifying questions
3. **Invalid session**: Returns appropriate error message
4. **Database errors**: Logs error and returns user-friendly message
5. **LLM failures**: Falls back to structured search

## Performance Considerations

- **Conversation history**: Limited to last 10 messages for context
- **Candidate results**: Returns top 10 in response, stores up to 50 in context
- **RAG search**: Default similarity threshold 0.4, adjustable
- **Caching**: Sessions and recent queries cached in memory
- **Async operations**: All I/O operations are async for better concurrency

## Future Enhancements

Potential improvements:

1. **Voice input**: Speech-to-text integration
2. **Advanced filters**: Date ranges, salary expectations, availability
3. **Saved searches**: Bookmark frequent queries
4. **Export results**: Download candidate lists as CSV/PDF
5. **Analytics**: Track popular queries and search patterns
6. **Multi-language**: Support for non-English queries
7. **Candidate scoring**: ML-based relevance scoring
8. **Notifications**: Alert when new matching candidates added

## Testing

Run the chat agent tests:

```bash
# Unit tests
pytest tests/test_cv_chat_agent.py -v

# Integration tests
pytest tests/integration/test_chat_api.py -v

# Test specific functionality
pytest tests/test_cv_chat_agent.py::test_query_understanding -v
```

## Monitoring

The agent logs all activities:

```python
from app.core.logging import rag_logger

# Logs include:
# - Query processing start/end
# - Intent detection results
# - Candidate retrieval counts
# - Response generation
# - Error details
```

## Troubleshooting

### Common Issues

1. **No candidates returned**
   - Check if CVs are indexed in the database
   - Lower similarity threshold
   - Verify embeddings are generated

2. **Slow responses**
   - Check OpenAI API latency
   - Optimize database queries
   - Enable query caching

3. **Context not maintained**
   - Verify session_id is passed consistently
   - Check message history is loading correctly

4. **Telegram integration issues**
   - Verify telegram_user_id format
   - Check session mapping logic
   - Review error logs

## Security Considerations

- **Authentication**: Add authentication middleware for production
- **Rate limiting**: Implement rate limits per user/session
- **Input validation**: All inputs validated by Pydantic schemas
- **SQL injection**: Protected by SQLAlchemy ORM
- **Data privacy**: Limit candidate data exposure in logs
- **API keys**: Never expose OpenAI keys in responses

## Related Documentation

- [HYBRID_MATCHING_ARCHITECTURE.md](./HYBRID_MATCHING_ARCHITECTURE.md) - CV matching architecture
- [MATCHER_QUICKSTART.md](./MATCHER_QUICKSTART.md) - Matcher agent guide
- [JOB_GENERATION_WORKFLOW.md](./JOB_GENERATION_WORKFLOW.md) - Job generation workflow

