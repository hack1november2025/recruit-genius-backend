#!/bin/bash
set -e

echo "🔄 Waiting for database to be ready..."

# Wait for PostgreSQL to be ready
until pg_isready -h "${DATABASE_HOST:-db}" -p "${DATABASE_PORT:-5432}" -U "${DATABASE_USER:-postgres}"; do
  echo "⏳ Waiting for PostgreSQL..."
  sleep 2
done

echo "✅ Database is ready!"

echo "🔧 Enabling pgvector extension..."
PGPASSWORD="${DATABASE_PASSWORD:-postgres}" psql -h "${DATABASE_HOST:-db}" -U "${DATABASE_USER:-postgres}" -d "${DATABASE_NAME:-recruitment}" -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "✅ pgvector extension enabled!"

echo "🔄 Running database migrations..."
alembic upgrade head

echo "✅ Migrations completed successfully!"

echo "🚀 Starting application..."
exec "$@"
