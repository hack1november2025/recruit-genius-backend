#!/bin/bash
# Quick start script for Docker deployment

set -e

echo "🚀 HR AI Recruitment Manager - Docker Quick Start"
echo "=================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Use docker compose or docker-compose (prefer docker compose)
DOCKER_COMPOSE="docker compose"
if ! docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
        echo ""
        echo "⚠️  IMPORTANT: Please edit .env and set your OPENAI_API_KEY before continuing!"
        echo ""
        read -p "Press Enter after you've updated .env with your API key..."
    else
        echo "❌ .env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Check if OPENAI_API_KEY is set
source .env
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-openai-api-key-here" ]; then
    echo "❌ OPENAI_API_KEY is not set in .env file."
    echo "Please edit .env and set a valid OpenAI API key."
    exit 1
fi

# Check if TELEGRAM_BOT_TOKEN is set
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your-telegram-bot-token-here" ]; then
    echo "⚠️ TELEGRAM_BOT_TOKEN is not set in .env file."
    echo "Please edit .env and set a valid Telegram bot token (if you plan to use the Telegram bot)."
fi
echo ""
echo "🔨 Building Docker images..."
$DOCKER_COMPOSE build

echo ""
echo "🚀 Starting services..."
$DOCKER_COMPOSE up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Wait for app to be healthy
echo "Checking application health..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo "✅ Application is healthy!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "⏳ Waiting for application... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Application failed to start. Check logs with: $DOCKER_COMPOSE logs app"
    exit 1
fi

echo ""
echo "✨ Success! Application is running."
echo ""
echo "📍 Endpoints:"
echo "   - API: http://localhost:8000"
echo "   - Swagger Docs: http://localhost:8000/docs"
echo "   - ReDoc: http://localhost:8000/redoc"
echo ""
echo "📊 View logs:"
echo "   $DOCKER_COMPOSE logs -f app"
echo ""
echo "🛑 Stop services:"
echo "   $DOCKER_COMPOSE down"
echo ""
echo "=================================================="
