# Docker Deployment Guide

This guide covers how to build and run the HR AI Recruitment Manager using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose V2
- OpenAI API Key

## Quick Start

### 1. Setup Environment Variables

Copy the example environment file and update with your values:

```bash
cp .env.example .env
```

**Important:** Edit `.env` and set your `OPENAI_API_KEY`:

```bash
OPENAI_API_KEY=sk-your-actual-openai-api-key
```

### 2. Build and Run with Docker Compose

Start all services (PostgreSQL, Redis, and the application):

```bash
docker-compose up -d
```

This will:
- Build the application Docker image
- Start PostgreSQL with pgvector extension
- Start Redis for caching
- Run database migrations automatically
- Start the FastAPI application

### 3. Check Application Status

```bash
# View logs
docker-compose logs -f app

# Check health
curl http://localhost:8000/api/v1/health
```

### 4. Access the Application

- **API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc

## Docker Commands

### Build and Start Services

```bash
# Build and start in detached mode
docker-compose up -d

# Build without cache
docker-compose build --no-cache

# Start specific service
docker-compose up -d app
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f db
docker-compose logs -f redis
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Run Migrations Manually

```bash
# Execute migrations in running container
docker-compose exec app alembic upgrade head

# Check current migration version
docker-compose exec app alembic current

# Create new migration
docker-compose exec app alembic revision --autogenerate -m "description"
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d recruitment

# Run SQL query
docker-compose exec db psql -U postgres -d recruitment -c "SELECT * FROM candidates LIMIT 5;"
```

### Redis Access

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Check Redis keys
docker-compose exec redis redis-cli KEYS "*"
```

## Build Docker Image Alone

If you want to build just the application image:

```bash
# Build image
docker build -t recruitment-app:latest .

# Run container (requires external database)
docker run -d \
  --name recruitment-app \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db" \
  -e OPENAI_API_KEY="your-key" \
  recruitment-app:latest
```

## Development Mode

For development with hot-reload, modify `docker-compose.yml`:

```yaml
app:
  # ... existing config ...
  environment:
    DEBUG: "true"
  volumes:
    - ./app:/app/app  # Mount source code
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Production Considerations

### 1. Environment Variables

- Never commit `.env` files with real credentials
- Use Docker secrets or external secret management
- Set `DEBUG=false` and `ENVIRONMENT=production`

### 2. Database

- Use managed PostgreSQL (e.g., AWS RDS, Azure Database)
- Configure proper backup strategy
- Set appropriate `DATABASE_POOL_SIZE` based on load

### 3. Security

- Configure CORS properly in `app/main.py`
- Use HTTPS/TLS in production
- Implement rate limiting
- Add authentication/authorization

### 4. Scaling

```bash
# Scale application instances
docker-compose up -d --scale app=3
```

### 5. Resource Limits

Add to `docker-compose.yml`:

```yaml
app:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

## Troubleshooting

### Application won't start

```bash
# Check logs
docker-compose logs app

# Check database connectivity
docker-compose exec app pg_isready -h db -U postgres

# Verify environment variables
docker-compose exec app env | grep DATABASE_URL
```

### Migration errors

```bash
# Check migration status
docker-compose exec app alembic current

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Port conflicts

If port 8000, 5432, or 6379 is already in use:

```yaml
# Modify docker-compose.yml ports
services:
  app:
    ports:
      - "8080:8000"  # Use different host port
```

### Permission errors

```bash
# Fix uploads directory permissions
sudo chown -R $(id -u):$(id -g) uploads/
chmod -R 755 uploads/
```

## Health Checks

The application includes health checks for all services:

- **App:** `curl http://localhost:8000/api/v1/health`
- **PostgreSQL:** Checked automatically by Docker
- **Redis:** Checked automatically by Docker

## Backup and Restore

### Backup Database

```bash
# Backup to file
docker-compose exec db pg_dump -U postgres recruitment > backup.sql

# Backup with docker-compose
docker-compose exec -T db pg_dump -U postgres recruitment | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore Database

```bash
# Restore from file
docker-compose exec -T db psql -U postgres recruitment < backup.sql

# Restore from gzipped backup
gunzip < backup.sql.gz | docker-compose exec -T db psql -U postgres recruitment
```

## Cleaning Up

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi recruitment-app:latest

# Remove all unused Docker resources
docker system prune -a --volumes
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Redis Docker Image](https://hub.docker.com/_/redis)
