# Docker Development Workflow Guide

**Last Updated: August 18, 2025**

## Overview

The AI Modernize Migration Platform uses a **Docker-First Development Model** where ALL development happens within containers. This ensures consistent environments across all developers and prevents "works on my machine" issues.

## Docker Architecture

### Service Overview

The platform consists of three main services orchestrated by Docker Compose:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│   Port: 8081    │    │   Port: 8000    │    │   Port: 5433    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Docker Compose Configuration

**Main Configuration File:** `/config/docker/docker-compose.yml`

```yaml
name: migration

services:
  # PostgreSQL Database with pgvector
  postgres:
    image: pgvector/pgvector:pg16
    container_name: migration_postgres
    environment:
      POSTGRES_DB: migration_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"  # External port 5433 to avoid conflicts
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 5s
      retries: 5
    networks:
      - migration_network

  # FastAPI Backend
  backend:
    build:
      context: ../..
      dockerfile: config/docker/Dockerfile.backend
    image: migrate-platform-backend:latest
    env_file:
      - ../../backend/.env
    container_name: migration_backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/migration_db
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - PYTHONUNBUFFERED=1
      - FRONTEND_URL=http://localhost:8081
      - ENVIRONMENT=development
      - DEBUG=true
      - PYTHONPATH=/app
      
      # Assessment Flow Configuration
      - ASSESSMENT_FLOW_ENABLED=true
      - CREWAI_ASSESSMENT_AGENTS_ENABLED=true
      - DEEPINFRA_ASSESSMENT_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct
      
      # Real-time Updates
      - SSE_ENABLED=true
      - SSE_HEARTBEAT_INTERVAL=30
      
      # Disable OpenTelemetry to prevent connection errors
      - OTEL_SDK_DISABLED=true
      - OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=all
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ../../backend:/app  # Live code reloading
    working_dir: /app
    networks:
      - migration_network

  # Frontend (Next.js)
  frontend:
    build:
      context: ../..
      dockerfile: config/docker/Dockerfile.frontend
    container_name: migration_frontend
    working_dir: /app
    environment:
      - DOCKER_ENV=true
      - VITE_WS_BASE_URL=ws://localhost:8000/ws
      - NODE_ENV=development
      - NPM_CONFIG_CACHE=/tmp/.npm
      - NPM_CONFIG_PREFIX=/tmp/.npm-global
    ports:
      - "8081:3000"  # Frontend runs on 8081 externally
    depends_on:
      - backend
    volumes:
      - ../../frontend:/app  # Live code reloading
      - /app/node_modules    # Exclude node_modules from volume
    networks:
      - migration_network

networks:
  migration_network:
    driver: bridge

volumes:
  postgres_data:
```

## Development Workflow

### 1. Starting the Development Environment

**Using Helper Scripts:**
```bash
# Start all services
./docker-start.sh

# Equivalent manual command
docker-compose -f config/docker/docker-compose.yml up -d
```

**Script Output:**
```
🚀 Starting AI Modernize Migration Platform with organized config structure...
Using docker-compose.yml from: config/docker/docker-compose.yml

✅ Services started successfully!

📊 Service Status:
NAME                  IMAGE                         COMMAND                  SERVICE    CREATED         STATUS                   PORTS
migration_postgres    pgvector/pgvector:pg16       "docker-entrypoint.s…"   postgres   4 seconds ago   Up 3 seconds (healthy)   0.0.0.0:5433->5432/tcp
migration_backend     migrate-platform-backend     "uvicorn app.main:ap…"   backend    4 seconds ago   Up 2 seconds             0.0.0.0:8000->8000/tcp
migration_frontend    migrate-platform-frontend    "npm run dev"            frontend   4 seconds ago   Up 1 second              0.0.0.0:8081->3000/tcp

🌐 Frontend: http://localhost:8081
🔧 Backend API: http://localhost:8000
🗄️  Database: localhost:5433
```

### 2. Service Management Commands

**View Service Status:**
```bash
docker-compose -f config/docker/docker-compose.yml ps
```

**View Real-time Logs:**
```bash
# All services
docker-compose -f config/docker/docker-compose.yml logs -f

# Specific service
docker-compose -f config/docker/docker-compose.yml logs -f backend
docker-compose -f config/docker/docker-compose.yml logs -f frontend
docker-compose -f config/docker/docker-compose.yml logs -f postgres
```

**Restart Services:**
```bash
# Restart all services
docker-compose -f config/docker/docker-compose.yml restart

# Restart specific service
docker-compose -f config/docker/docker-compose.yml restart backend
```

**Stop Services:**
```bash
# Stop all services (preserves data)
./docker-stop.sh

# Equivalent manual command
docker-compose -f config/docker/docker-compose.yml down

# Stop and remove volumes (DANGER: removes all data)
docker-compose -f config/docker/docker-compose.yml down -v
```

### 3. Development Hot Reloading

**Backend Hot Reloading:**
The backend uses volume mounting for live code reloading:

```yaml
volumes:
  - ../../backend:/app  # Maps local backend code to container
```

Changes to Python files automatically trigger FastAPI to reload:
```bash
# Watch backend logs to see reloading
docker-compose -f config/docker/docker-compose.yml logs -f backend

# Example output when files change:
# INFO:     Will watch for changes in these directories: ['/app']
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process [1] using StatReload
# INFO:     Started server process [8]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
```

**Frontend Hot Reloading:**
The frontend uses Next.js development server with hot module replacement:

```yaml
volumes:
  - ../../frontend:/app     # Maps local frontend code
  - /app/node_modules       # Excludes node_modules from sync
```

Changes to React/TypeScript files automatically update in browser.

## Container Images

### 1. Backend Dockerfile

**File:** `/config/docker/Dockerfile.backend`

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 2. Frontend Dockerfile

**File:** `/config/docker/Dockerfile.frontend`

```dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci --only=production=false

# Copy application code
COPY frontend/ .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Start development server
CMD ["npm", "run", "dev"]
```

## Environment Configuration

### 1. Backend Environment Variables

**File:** `/backend/.env`

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/migration_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=migration_db

# Application Configuration
ENVIRONMENT=development
DEBUG=true
API_V1_STR=/api/v1
SECRET_KEY=your-secret-key-here
PYTHONPATH=/app

# Frontend Configuration
FRONTEND_URL=http://localhost:8081

# CrewAI Configuration
DEEPINFRA_API_KEY=your-deepinfra-key
DEEPINFRA_ASSESSMENT_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct
CREWAI_ASSESSMENT_AGENTS_ENABLED=true

# Flow Configuration
ASSESSMENT_FLOW_ENABLED=true
ASSESSMENT_CREW_PARALLELISM=3
ASSESSMENT_TIMEOUT_MINUTES=30
ASSESSMENT_MAX_CONCURRENT_FLOWS=5
ASSESSMENT_COMPONENT_BATCH_SIZE=10

# Real-time Configuration
SSE_ENABLED=true
SSE_HEARTBEAT_INTERVAL=30

# Observability (Disabled in Development)
OTEL_SDK_DISABLED=true
OTEL_TRACES_EXPORTER=none
OTEL_METRICS_EXPORTER=none
OTEL_LOGS_EXPORTER=none
OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=all

# Discovery Flow Configuration
USE_FAST_DISCOVERY_MODE=false
```

### 2. Frontend Environment Variables

**File:** `/frontend/.env.local`

```env
# Docker environment indicator
DOCKER_ENV=true

# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/ws

# Development Configuration
NODE_ENV=development
NEXT_PUBLIC_ENV=development

# NPM Configuration (prevents cache issues)
NPM_CONFIG_CACHE=/tmp/.npm
NPM_CONFIG_PREFIX=/tmp/.npm-global
```

## Database Management

### 1. Database Connection

**Connection Details:**
```
Host: localhost
Port: 5433 (externally mapped from container port 5432)
Database: migration_db
Username: postgres
Password: postgres
```

**Connection String:**
```
postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db
```

### 2. Database Operations

**Connect to Database:**
```bash
# Using psql from host (if installed)
psql -h localhost -p 5433 -U postgres -d migration_db

# Using psql from container
docker exec -it migration_postgres psql -U postgres -d migration_db
```

**Run Migrations:**
```bash
# Enter backend container
docker exec -it migration_backend bash

# Run Alembic migrations
cd /app
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description of changes"
```

**Database Backup/Restore:**
```bash
# Backup database
docker exec migration_postgres pg_dump -U postgres migration_db > backup.sql

# Restore database
docker exec -i migration_postgres psql -U postgres migration_db < backup.sql

# Reset database (DANGER: removes all data)
docker exec migration_postgres psql -U postgres -c "DROP DATABASE IF EXISTS migration_db; CREATE DATABASE migration_db;"
```

### 3. Seeding Development Data

**Automatic Seeding:**
The backend automatically seeds demo data on startup in development mode.

**Manual Seeding:**
```bash
# Enter backend container
docker exec -it migration_backend bash

# Run seeding scripts
python seeding/01_core_entities.py
python seeding/02_discovery_flows.py
python seeding/03_data_imports.py
```

## Development Commands

### 1. Backend Development

**Enter Backend Container:**
```bash
docker exec -it migration_backend bash
```

**Run Tests:**
```bash
# Inside backend container
pytest tests/ -v
pytest tests/test_specific.py -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html
```

**Code Quality:**
```bash
# Linting
flake8 app/
black app/ --check
isort app/ --check-only

# Fix formatting
black app/
isort app/
```

**Install New Dependencies:**
```bash
# Add to requirements.txt then rebuild
docker-compose -f config/docker/docker-compose.yml build backend
docker-compose -f config/docker/docker-compose.yml up -d backend
```

### 2. Frontend Development

**Enter Frontend Container:**
```bash
docker exec -it migration_frontend sh
```

**Install New Dependencies:**
```bash
# Inside frontend container
npm install package-name

# Or rebuild container
docker-compose -f config/docker/docker-compose.yml build frontend
docker-compose -f config/docker/docker-compose.yml up -d frontend
```

**Run Frontend Tests:**
```bash
# Inside frontend container
npm test
npm run test:e2e
```

**Build for Production:**
```bash
# Inside frontend container
npm run build
npm run start
```

## Debugging

### 1. Service Health Checks

**Check Service Health:**
```bash
# Backend health
curl http://localhost:8000/health

# Database health
docker exec migration_postgres pg_isready -U postgres

# Frontend health (if health endpoint exists)
curl http://localhost:8081/api/health
```

**View Container Stats:**
```bash
# Resource usage
docker stats migration_postgres migration_backend migration_frontend

# Container inspection
docker inspect migration_backend
```

### 2. Log Analysis

**Backend Logs:**
```bash
# Follow backend logs
docker-compose -f config/docker/docker-compose.yml logs -f backend

# Search logs for errors
docker-compose -f config/docker/docker-compose.yml logs backend | grep ERROR

# Filter logs by timestamp
docker-compose -f config/docker/docker-compose.yml logs --since="2025-08-18T10:00:00" backend
```

**Database Logs:**
```bash
# PostgreSQL logs
docker-compose -f config/docker/docker-compose.yml logs -f postgres

# Query performance logs
docker exec migration_postgres psql -U postgres -d migration_db -c "SELECT * FROM pg_stat_activity;"
```

### 3. Network Debugging

**Container Network:**
```bash
# Inspect network
docker network inspect migration_migration_network

# Test connectivity between containers
docker exec migration_backend ping postgres
docker exec migration_frontend ping migration_backend
```

**Port Mapping:**
```bash
# Verify port mappings
docker port migration_backend
docker port migration_frontend
docker port migration_postgres
```

## Performance Optimization

### 1. Docker Performance

**Resource Limits:**
```yaml
# Add to docker-compose.yml services
backend:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
```

**Volume Optimization:**
```yaml
# Use bind mounts for development, volumes for data
volumes:
  - ../../backend:/app:cached  # Cached for better performance on macOS
  - backend_node_modules:/app/node_modules  # Named volume for node_modules
```

### 2. Build Optimization

**Multi-stage Builds:**
```dockerfile
# Dockerfile.backend.optimized
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

WORKDIR /app
COPY . .

ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Layer Caching:**
```dockerfile
# Order commands for better caching
COPY requirements.txt .          # Changes less frequently
RUN pip install -r requirements.txt
COPY . .                        # Changes more frequently
```

## Troubleshooting

### 1. Common Issues

**Port Already in Use:**
```bash
# Check what's using the port
lsof -i :8000
lsof -i :8081
lsof -i :5433

# Kill processes using the port
kill -9 $(lsof -t -i:8000)
```

**Database Connection Issues:**
```bash
# Check database logs
docker-compose -f config/docker/docker-compose.yml logs postgres

# Verify database is ready
docker exec migration_postgres pg_isready -U postgres

# Reset database connection
docker-compose -f config/docker/docker-compose.yml restart postgres backend
```

**Container Build Failures:**
```bash
# Clean build cache
docker system prune -f
docker builder prune -f

# Rebuild without cache
docker-compose -f config/docker/docker-compose.yml build --no-cache
```

### 2. Volume Issues

**File Permission Problems:**
```bash
# Fix permissions on mounted volumes
sudo chown -R $USER:$USER backend/
sudo chown -R $USER:$USER frontend/

# Use user mapping in docker-compose
backend:
  user: "${UID}:${GID}"
```

**Volume Sync Issues:**
```bash
# Force volume recreation
docker-compose -f config/docker/docker-compose.yml down -v
docker-compose -f config/docker/docker-compose.yml up -d
```

### 3. Memory/CPU Issues

**Resource Monitoring:**
```bash
# Monitor container resources
docker stats --no-stream

# Check system resources
free -h
df -h
```

**Memory Optimization:**
```bash
# Clear Docker cache
docker system prune -f

# Restart Docker daemon (if needed)
sudo systemctl restart docker
```

## Production Considerations

### 1. Environment Differences

**Development vs Production:**
```yaml
# docker-compose.prod.yml
services:
  backend:
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - RELOAD=false
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    # Remove volume mounts for production
```

### 2. Security Hardening

**Production Security:**
```dockerfile
# Use non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# Remove unnecessary packages
RUN apt-get remove -y gcc g++ && apt-get autoremove -y
```

**Environment Variables:**
```bash
# Use Docker secrets in production
docker secret create postgres_password /path/to/password/file
```

This comprehensive Docker development guide ensures smooth development workflows while maintaining consistency across all development environments.