#!/bin/bash

# Test job generator agent - Create and save a job description

echo "🧪 Testing Job Generator Agent - Create and Save Job"
echo "=================================================="
echo ""

# Generate a unique thread ID
THREAD_ID="test-job-$(date +%s)"

echo "Thread ID: $THREAD_ID"
echo ""

# Step 1: Ask agent to create a job
echo "📝 Step 1: Requesting job description for Python Developer..."
RESPONSE1=$(curl -s -X POST "http://localhost:8000/api/v1/job-descriptions/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Create a job description for a Senior Python Developer with 5 years experience\"
  }")

echo "$RESPONSE1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['response'][:500]); THREAD_ID=data['thread_id']"
echo ""
echo "..."
echo ""

# Extract thread_id from first response
THREAD_ID=$(echo "$RESPONSE1" | python3 -c "import sys, json; print(json.load(sys.stdin)['thread_id'])")
echo "Using thread_id: $THREAD_ID"
echo ""

# Step 2: Approve and save the job
echo "✅ Step 2: Approving and saving the job..."
RESPONSE2=$(curl -s -X POST "http://localhost:8000/api/v1/job-descriptions/chat?thread_id=$THREAD_ID" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"looks good, save it\"
  }")

echo "$RESPONSE2" | python3 -c "import sys, json; print(json.load(sys.stdin)['response'])"
echo ""

# Check for success or error
if echo "$RESPONSE2" | grep -q "✅ Job successfully created"; then
    echo ""
    echo "🎉 SUCCESS! Job was created and saved to database!"
    
    # Extract job ID
    JOB_ID=$(echo "$RESPONSE2" | grep -oP 'ID \K[0-9]+' | head -1)
    if [ ! -z "$JOB_ID" ]; then
        echo "📋 Job ID: $JOB_ID"
    fi
elif echo "$RESPONSE2" | grep -q "❌ Failed to save job"; then
    echo ""
    echo "❌ FAILED! Job save operation failed"
else
    echo ""
    echo "⚠️  UNKNOWN STATUS"
fi

echo ""
echo "=================================================="
