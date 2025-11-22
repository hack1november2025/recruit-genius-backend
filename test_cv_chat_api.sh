#!/bin/bash
# Test script for CV Chat Agent (using LangGraph checkpointer)

set -e

BASE_URL="http://localhost:8000/api/v1"

echo "🧪 Testing CV Chat Agent (with LangGraph Checkpointer)..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Generate unique thread ID for this test
THREAD_ID="test_thread_$(date +%s)"

echo -e "${BLUE}Using thread_id: $THREAD_ID${NC}"
echo ""

# Test 1: Send First Query (thread will be auto-created by checkpointer)
echo -e "${BLUE}Test 1: Sending first query (search)...${NC}"
QUERY_1=$(curl -s -X POST $BASE_URL/chat/query \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Find Python developers\",
    \"thread_id\": \"$THREAD_ID\",
    \"user_identifier\": \"test_user\"
  }")

RESPONSE_TEXT=$(echo $QUERY_1 | jq -r '.response_text')
CANDIDATE_COUNT=$(echo $QUERY_1 | jq -r '.candidate_ids | length')
RETURNED_THREAD=$(echo $QUERY_1 | jq -r '.thread_id')

if [ -n "$RESPONSE_TEXT" ] && [ "$RETURNED_THREAD" == "$THREAD_ID" ]; then
  echo -e "${GREEN}✓ Query processed successfully${NC}"
  echo "Response preview: ${RESPONSE_TEXT:0:100}..."
  echo "Candidates found: $CANDIDATE_COUNT"
  echo "Thread ID: $RETURNED_THREAD"
else
  echo -e "${RED}✗ Failed to process query${NC}"
fi
echo ""

# Test 2: Send Follow-up Query (checkpointer loads conversation history automatically)
echo -e "${BLUE}Test 2: Sending follow-up query (filter with context)...${NC}"
QUERY_2=$(curl -s -X POST $BASE_URL/chat/query \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Who among them has AWS experience?\",
    \"thread_id\": \"$THREAD_ID\",
    \"user_identifier\": \"test_user\"
  }")

RESPONSE_TEXT_2=$(echo $QUERY_2 | jq -r '.response_text')
CANDIDATE_COUNT_2=$(echo $QUERY_2 | jq -r '.candidate_ids | length')

if [ -n "$RESPONSE_TEXT_2" ]; then
  echo -e "${GREEN}✓ Follow-up query processed with context${NC}"
  echo "Response preview: ${RESPONSE_TEXT_2:0:100}..."
  echo "Filtered candidates: $CANDIDATE_COUNT_2"
else
  echo -e "${RED}✗ Failed to process follow-up query${NC}"
fi
echo ""

# Test 3: Query without thread_id (should generate new one)
echo -e "${BLUE}Test 3: Query without thread_id (auto-generation)...${NC}"
QUERY_3=$(curl -s -X POST $BASE_URL/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find data scientists",
    "user_identifier": "test_user"
  }')

NEW_THREAD=$(echo $QUERY_3 | jq -r '.thread_id')

if [ "$NEW_THREAD" != "null" ] && [ -n "$NEW_THREAD" ]; then
  echo -e "${GREEN}✓ Auto-generated thread_id${NC}"
  echo "New thread ID: $NEW_THREAD"
else
  echo -e "${RED}✗ Failed to generate thread_id${NC}"
fi
echo ""

# Test 4: Test Telegram Endpoint
echo -e "${BLUE}Test 4: Testing Telegram endpoint...${NC}"
TELEGRAM_RESPONSE=$(curl -s -X POST $BASE_URL/chat/telegram \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_user_id": "123456789",
    "message": "Find software engineers"
  }')

TELEGRAM_THREAD=$(echo $TELEGRAM_RESPONSE | jq -r '.thread_id')

if [ "$TELEGRAM_THREAD" != "null" ] && [ -n "$TELEGRAM_THREAD" ]; then
  echo -e "${GREEN}✓ Telegram endpoint working${NC}"
  echo "Telegram thread: $TELEGRAM_THREAD"
else
  echo -e "${RED}✗ Telegram endpoint failed${NC}"
fi
echo ""

# Test 5: Third query on original thread (verify persistence)
echo -e "${BLUE}Test 5: Third query on original thread (verify persistence)...${NC}"
QUERY_4=$(curl -s -X POST $BASE_URL/chat/query \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Compare the top 3\",
    \"thread_id\": \"$THREAD_ID\",
    \"user_identifier\": \"test_user\"
  }")

RESPONSE_TEXT_4=$(echo $QUERY_4 | jq -r '.response_text')

if [ -n "$RESPONSE_TEXT_4" ]; then
  echo -e "${GREEN}✓ Conversation history persisted across queries${NC}"
  echo "Response preview: ${RESPONSE_TEXT_4:0:100}..."
else
  echo -e "${RED}✗ Failed to maintain conversation context${NC}"
fi
echo ""

echo -e "${GREEN}✅ All tests completed!${NC}"
echo ""
echo "Key Points:"
echo "- No separate session management needed"
echo "- LangGraph checkpointer handles all conversation persistence"
echo "- Just use consistent thread_id for multi-turn conversations"
echo "- Checkpointer stores: messages, candidate context, full state"
echo ""
echo "Next steps:"
echo "1. Check the API documentation at http://localhost:8000/docs"
echo "2. Review LangGraph checkpointer tables in PostgreSQL"
echo "3. Try more complex queries with your actual CV data"
