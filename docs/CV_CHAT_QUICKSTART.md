# CV Chat Agent - Quick Start Guide

## Overview

The CV Chat Agent enables HR personnel to query the CV database using natural language. This guide shows you how to get started quickly.

## Prerequisites

1. Backend server running with database migrations applied
2. CVs uploaded and processed (indexed in vector database)
3. OpenAI API key configured in `.env`

## Quick Test with curl

### 1. Create a Chat Session

```bash
curl -X POST http://localhost:8000/api/v1/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"session_name": "Test Search"}'
```

Response:
```json
{
  "id": 1,
  "session_name": "Test Search",
  "created_at": "2025-11-22T10:00:00Z",
  "updated_at": "2025-11-22T10:00:00Z",
  "message_count": 0
}
```

### 2. Send a Query

```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find senior Python developers in London",
    "session_id": 1,
    "user_identifier": "test_user"
  }'
```

Response:
```json
{
  "session_id": 1,
  "response_text": "I found 5 senior Python developers in London. Here are the top matches:\n\n1. John Doe - 7 years of experience with Python, Django, and AWS...",
  "structured_response": {
    "type": "candidates",
    "candidates": [
      {
        "candidate_id": 42,
        "name": "John Doe",
        "email": "john@example.com",
        "skills": ["Python", "Django", "PostgreSQL"],
        "experience_years": 7,
        "location": "London, UK",
        "similarity_score": 0.87
      }
    ],
    "total_count": 5
  },
  "candidate_ids": [42, 43, 44, 45, 46]
}
```

### 3. Send a Follow-up Query

```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who among them has AWS experience?",
    "session_id": 1,
    "user_identifier": "test_user"
  }'
```

The agent will remember the previous candidates and filter them based on AWS experience.

## Query Examples

### Basic Search
```
"Find Python developers"
"Show me software engineers with 5+ years experience"
"Find candidates with machine learning skills"
```

### Filtered Search
```
"Find senior Python developers in London"
"Show me data scientists with PhD degrees"
"Find frontend developers who know React and TypeScript"
```

### Follow-up Queries
```
"Who among them has AWS experience?"
"Filter by startup experience"
"Show only those with 5+ years"
```

### Comparison
```
"Compare the top 3 candidates"
"Show me differences between candidates 42 and 43"
```

### Specific Information
```
"What are John Doe's programming languages?"
"Tell me more about the first candidate"
"What companies has candidate 42 worked at?"
```

## Web UI Integration Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>CV Chat</title>
</head>
<body>
    <div id="chat">
        <div id="messages"></div>
        <input id="query" type="text" placeholder="Ask about candidates...">
        <button onclick="sendQuery()">Send</button>
    </div>

    <script>
        let sessionId = null;

        async function createSession() {
            const response = await fetch('/api/v1/chat/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_name: 'Web Chat' })
            });
            const data = await response.json();
            sessionId = data.id;
        }

        async function sendQuery() {
            if (!sessionId) await createSession();
            
            const query = document.getElementById('query').value;
            
            const response = await fetch('/api/v1/chat/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    session_id: sessionId,
                    user_identifier: 'web_user'
                })
            });
            
            const data = await response.json();
            
            // Display user message
            addMessage('user', query);
            
            // Display assistant response
            addMessage('assistant', data.response_text);
            
            // Display candidates if any
            if (data.structured_response.candidates) {
                displayCandidates(data.structured_response.candidates);
            }
            
            document.getElementById('query').value = '';
        }

        function addMessage(role, content) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = role;
            messageDiv.textContent = content;
            messagesDiv.appendChild(messageDiv);
        }

        function displayCandidates(candidates) {
            candidates.forEach(candidate => {
                const div = document.createElement('div');
                div.className = 'candidate';
                div.innerHTML = `
                    <h4>${candidate.name}</h4>
                    <p>Email: ${candidate.email}</p>
                    <p>Skills: ${candidate.skills.join(', ')}</p>
                    <p>Experience: ${candidate.experience_years} years</p>
                    <p>Location: ${candidate.location}</p>
                `;
                document.getElementById('messages').appendChild(div);
            });
        }
    </script>
</body>
</html>
```

## Python Client Example

```python
import asyncio
import httpx

class CVChatClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
    
    async def create_session(self, name="Python Client Session"):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/chat/sessions",
                json={"session_name": name}
            )
            data = response.json()
            self.session_id = data["id"]
            return data
    
    async def query(self, text):
        if not self.session_id:
            await self.create_session()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/chat/query",
                json={
                    "query": text,
                    "session_id": self.session_id,
                    "user_identifier": "python_client"
                }
            )
            return response.json()
    
    async def get_history(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/chat/sessions/{self.session_id}"
            )
            return response.json()

# Usage
async def main():
    client = CVChatClient()
    
    # First query
    result = await client.query("Find senior Python developers")
    print(result["response_text"])
    print(f"Found {len(result['candidate_ids'])} candidates")
    
    # Follow-up query
    result = await client.query("Who among them has AWS experience?")
    print(result["response_text"])
    
    # Get full history
    history = await client.get_history()
    print(f"Total messages: {len(history['messages'])}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Telegram Bot Integration

### Setup Telegram Webhook

1. Create a Telegram bot via [@BotFather](https://t.me/botfather)
2. Get your bot token
3. Set webhook to your server:

```bash
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -d "url=https://your-domain.com/telegram/webhook"
```

### Handle Telegram Messages

```python
from fastapi import FastAPI, Request
from app.schemas.chat import TelegramChatRequest

app = FastAPI()

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    # Extract message details
    message = data.get("message", {})
    telegram_user_id = str(message["from"]["id"])
    text = message.get("text", "")
    
    # Process through CV chat agent
    chat_request = TelegramChatRequest(
        telegram_user_id=telegram_user_id,
        message=text,
        session_id=None  # Will auto-create per user
    )
    
    async with get_db() as db:
        response = await process_telegram_query(chat_request, db)
    
    # Send response back to Telegram
    await send_telegram_message(
        telegram_user_id,
        response.response_text
    )
    
    # Send candidate cards if any
    for candidate in response.candidates[:5]:
        await send_candidate_card(telegram_user_id, candidate)
    
    return {"ok": True}
```

## Testing the Agent

### Test Script

Save as `test_cv_chat.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000/api/v1"

# Create session
SESSION=$(curl -s -X POST $BASE_URL/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"session_name": "Test"}' | jq -r '.id')

echo "Created session: $SESSION"

# Test queries
queries=(
  "Find Python developers"
  "Who among them has AWS experience?"
  "Compare the top 3"
  "What skills does the first candidate have?"
)

for query in "${queries[@]}"; do
  echo -e "\n=== Query: $query ==="
  curl -s -X POST $BASE_URL/chat/query \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$query\", \"session_id\": $SESSION, \"user_identifier\": \"test\"}" \
    | jq -r '.response_text'
done

# Get history
echo -e "\n=== Chat History ==="
curl -s $BASE_URL/chat/sessions/$SESSION | jq '.messages | length'
echo "messages in conversation"
```

Run:
```bash
chmod +x test_cv_chat.sh
./test_cv_chat.sh
```

## Common Issues

### No Candidates Found

**Problem**: Query returns no candidates

**Solutions**:
1. Check if CVs are processed: `SELECT COUNT(*) FROM cvs WHERE is_processed = true;`
2. Verify embeddings exist: `SELECT COUNT(*) FROM cv_embeddings;`
3. Lower similarity threshold in query
4. Try broader search terms

### Slow Response

**Problem**: Queries take too long

**Solutions**:
1. Check OpenAI API latency
2. Add database indexes
3. Reduce conversation history length
4. Enable response caching

### Context Not Maintained

**Problem**: Follow-up queries don't use previous context

**Solutions**:
1. Always use the same `session_id`
2. Check message history is loading correctly
3. Verify `candidate_ids_in_context` is populated

## Next Steps

1. **Explore API docs**: Visit `http://localhost:8000/docs`
2. **Read full documentation**: See [CV_CHAT_AGENT.md](./CV_CHAT_AGENT.md)
3. **Test with your data**: Upload CVs and try different queries
4. **Build frontend**: Create a chat UI for your users
5. **Add Telegram bot**: Enable mobile access via Telegram

## Support

- Check logs: `tail -f logs/app.log`
- Enable debug mode: `DEBUG=true` in `.env`
- Review conversation history in database
- Test with curl before integrating

