#!/bin/bash
# Quick test script for the conversational job generator API

BASE_URL="http://localhost:8000/api/v1/job-descriptions"

echo "======================================"
echo "Testing Conversational Job Generator"
echo "======================================"
echo ""

# Test 1: Create new job description
echo "TEST 1: Creating job description..."
RESPONSE=$(curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a job posting for senior Python developer with 5 years experience"}')

THREAD_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['thread_id'])")
echo "Thread ID: $THREAD_ID"
echo "Response:"
echo $RESPONSE | python3 -m json.tool
echo ""

# Test 2: Request modification
echo "TEST 2: Requesting modification..."
curl -s -X POST "$BASE_URL/chat?thread_id=$THREAD_ID" \
  -H "Content-Type: application/json" \
  -d '{"message": "Make it more friendly and emphasize remote work"}' | python3 -m json.tool
echo ""

# Test 3: Save to database
echo "TEST 3: Saving to database..."
curl -s -X POST "$BASE_URL/chat?thread_id=$THREAD_ID" \
  -H "Content-Type: application/json" \
  -d '{"message": "Save this job with title Senior Python Developer, department Engineering"}' | python3 -m json.tool
echo ""

echo "======================================"
echo "All tests completed!"
echo "======================================"
