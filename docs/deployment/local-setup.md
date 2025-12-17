# Local Development Setup Guide

**Last Updated: August 18, 2025**

## Overview

This guide provides comprehensive step-by-step instructions for setting up the AI Modernize Migration Platform for local development. The platform follows a **Docker-First Development Model**, so all development happens within containers.

## Prerequisites

### System Requirements

**Minimum Hardware:**
- CPU: 4 cores (8 cores recommended)
- RAM: 8GB (16GB recommended) 
- Storage: 20GB free space (SSD recommended)
- Network: Stable internet connection for container downloads

**Operating Systems:**
- macOS 10.15+ (Catalina or later)
- Windows 10/11 with WSL2
- Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)

### Required Software

**Docker & Docker Compose:**
```bash
# macOS (using Homebrew)
brew install docker docker-compose
# Or install Docker Desktop from https://docker.com

# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER

# CentOS/RHEL
sudo yum install docker docker-compose
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Windows
# Install Docker Desktop from https://docker.com
# Ensure WSL2 backend is enabled
```

**Git:**
```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt install git

# CentOS/RHEL
sudo yum install git

# Windows
# Install Git for Windows from https://git-scm.com
```

**Optional Tools (Recommended):**
```bash
# PostgreSQL client (for database access)
# macOS
brew install postgresql

# Ubuntu/Debian
sudo apt install postgresql-client

# VS Code with Docker extension
# Download from https://code.visualstudio.com/
```

## Step-by-Step Setup

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-org/migrate-ui-orchestrator.git
cd migrate-ui-orchestrator

# Verify repository structure
ls -la
# Should see: backend/, frontend/, config/, docs/, etc.
```

### Step 2: Environment Configuration

**Create Backend Environment File:**
```bash
# Copy template and customize
cp backend/.env.example backend/.env

# Edit the environment file
nano backend/.env  # or use your preferred editor
```

**Backend Environment Variables (`backend/.env`):**
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
SECRET_KEY=your-super-secret-key-change-this-in-production
PYTHONPATH=/app

# Frontend Configuration
FRONTEND_URL=http://localhost:8081

# AI Configuration (Replace with your actual keys)
DEEPINFRA_API_KEY=your-deepinfra-api-key-here
OPENAI_API_KEY=your-openai-api-key-here  # Optional
DEEPINFRA_ASSESSMENT_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct

# Google Gemini Configuration (Optional - for Gemini model support)
GOOGLE_GEMINI_API_KEY=your-google-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-pro

# CrewAI Configuration
CREWAI_ASSESSMENT_AGENTS_ENABLED=true
ASSESSMENT_FLOW_ENABLED=true
ASSESSMENT_CREW_PARALLELISM=3
ASSESSMENT_TIMEOUT_MINUTES=30

# Real-time Features
SSE_ENABLED=true
SSE_HEARTBEAT_INTERVAL=30

# Performance Settings
ASSESSMENT_MAX_CONCURRENT_FLOWS=5
ASSESSMENT_COMPONENT_BATCH_SIZE=10
USE_FAST_DISCOVERY_MODE=false

# Observability (Disabled for development)
OTEL_SDK_DISABLED=true
OTEL_TRACES_EXPORTER=none
OTEL_METRICS_EXPORTER=none
OTEL_LOGS_EXPORTER=none
OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=all

# Demo Mode Configuration
DEMO_MODE=true
DEMO_CLIENT_ID=11111111-1111-1111-1111-111111111111
DEMO_ENGAGEMENT_ID=22222222-2222-2222-2222-222222222222
```

**Create Frontend Environment File:**
```bash
# Create frontend environment file
cp frontend/.env.example frontend/.env.local

# Edit frontend environment
nano frontend/.env.local
```

**Frontend Environment Variables (`frontend/.env.local`):**
```env
# Docker environment indicator
DOCKER_ENV=true

# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/ws

# Development Configuration
NODE_ENV=development
NEXT_PUBLIC_ENV=development

# NPM Configuration (prevents cache issues in Docker)
NPM_CONFIG_CACHE=/tmp/.npm
NPM_CONFIG_PREFIX=/tmp/.npm-global

# Feature Flags
NEXT_PUBLIC_ASSESSMENT_FLOW_ENABLED=true
NEXT_PUBLIC_REAL_TIME_ENABLED=true
```

### Step 3: Verify Docker Installation

```bash
# Check Docker version
docker --version
# Should output: Docker version 20.x.x or higher

# Check Docker Compose version
docker-compose --version
# Should output: Docker Compose version 2.x.x or higher

# Test Docker installation
docker run hello-world
# Should successfully download and run the hello-world container
```

### Step 4: Build and Start Services

**Option A: Using Helper Scripts (Recommended)**
```bash
# Make scripts executable (Linux/macOS)
chmod +x docker-start.sh docker-stop.sh

# Start all services
./docker-start.sh

# Expected output:
# 🚀 Starting AI Modernize Migration Platform with organized config structure...
# Using docker-compose.yml from: config/docker/docker-compose.yml
# 
# ✅ Services started successfully!
# 
# 📊 Service Status:
# NAME                  IMAGE                         COMMAND                  SERVICE    CREATED         STATUS                   PORTS
# migration_postgres    pgvector/pgvector:pg16       "docker-entrypoint.s…"   postgres   4 seconds ago   Up 3 seconds (healthy)   0.0.0.0:5433->5432/tcp
# migration_backend     migrate-platform-backend     "uvicorn app.main:ap…"   backend    4 seconds ago   Up 2 seconds             0.0.0.0:8000->8000/tcp
# migration_frontend    migrate-platform-frontend    "npm run dev"            frontend   4 seconds ago   Up 1 second              0.0.0.0:8081->8081/tcp
# 
# 🌐 Frontend: http://localhost:8081
# 🔧 Backend API: http://localhost:8000
# 🗄️  Database: localhost:5433
```

**Option B: Manual Docker Compose Commands**
```bash
# Start services manually
docker-compose -f config/docker/docker-compose.yml up -d

# Check service status
docker-compose -f config/docker/docker-compose.yml ps

# View logs
docker-compose -f config/docker/docker-compose.yml logs -f
```

### Step 5: Verify Services are Running

**Check Service Health:**
```bash
# Backend health check
curl http://localhost:8000/health
# Expected: {"status": "healthy", "timestamp": "2025-08-18T..."}

# Frontend accessibility
curl http://localhost:8081
# Expected: HTML response from Next.js

# Database connectivity
docker exec migration_postgres pg_isready -U postgres
# Expected: /var/run/postgresql:5432 - accepting connections
```

**Check Service Logs:**
```bash
# View all service logs
docker-compose -f config/docker/docker-compose.yml logs

# View specific service logs
docker-compose -f config/docker/docker-compose.yml logs backend
docker-compose -f config/docker/docker-compose.yml logs frontend
docker-compose -f config/docker/docker-compose.yml logs postgres
```

### Step 6: Database Initialization

**Automatic Initialization:**
The database is automatically initialized when the backend starts for the first time.

**Manual Database Setup (if needed):**
```bash
# Enter backend container
docker exec -it migration_backend bash

# Inside the container, run migrations
alembic upgrade head

# Seed demo data
python seeding/01_core_entities.py
python seeding/02_discovery_flows.py
python seeding/03_data_imports.py

# Exit container
exit
```

**Verify Database Setup:**
```bash
# Connect to database
docker exec -it migration_postgres psql -U postgres -d migration_db

# Check tables
\dt

# Expected tables:
# client_accounts, engagements, users, discovery_flows, 
# crewai_flow_state_extensions, assets, etc.

# Exit psql
\q
```

### Step 7: Access the Application

**Frontend Application:**
- URL: http://localhost:8081
- Default credentials: Demo mode (no login required)

**Backend API:**
- URL: http://localhost:8000
- API Documentation: http://localhost:8000/docs (Swagger UI)
- Health Check: http://localhost:8000/health

**Database:**
- Host: localhost
- Port: 5433
- Database: migration_db
- Username: postgres
- Password: postgres

## Development Workflow

### Hot Reloading

**Backend Hot Reloading:**
```bash
# Backend automatically reloads when Python files change
# Watch the logs to see reload messages
docker-compose -f config/docker/docker-compose.yml logs -f backend

# Make a change to a Python file and observe:
# INFO:     Will watch for changes in these directories: ['/app']
# INFO:     Detected file change in 'app/main.py'
# INFO:     Restarting...
```

**Frontend Hot Reloading:**
```bash
# Frontend automatically reloads when React/TypeScript files change
# Watch the logs to see reload messages
docker-compose -f config/docker/docker-compose.yml logs -f frontend

# Make a change to a React component and observe browser refresh
```

### Making Code Changes

**Backend Development:**
```bash
# All Python files in backend/ are mapped to the container
# Changes are immediately reflected without rebuilding

# Example: Edit a route
nano backend/app/api/v1/endpoints/health.py

# Save the file - FastAPI will automatically reload
```

**Frontend Development:**
```bash
# All frontend files are mapped to the container
# Changes trigger Next.js hot module replacement

# Example: Edit a React component
nano frontend/src/components/Dashboard.tsx

# Save the file - browser will automatically refresh
```

### Installing New Dependencies

**Backend Dependencies:**
```bash
# Add package to requirements.txt
echo "new-package==1.0.0" >> backend/requirements.txt

# Rebuild backend container
docker-compose -f config/docker/docker-compose.yml build backend
docker-compose -f config/docker/docker-compose.yml up -d backend
```

**Frontend Dependencies:**
```bash
# Enter frontend container
docker exec -it migration_frontend sh

# Install new package
npm install new-package

# Or rebuild container if package.json was modified
docker-compose -f config/docker/docker-compose.yml build frontend
docker-compose -f config/docker/docker-compose.yml up -d frontend
```

## API Configuration and Testing

### API Key Setup

**DeepInfra API Key (Required for AI Features):**
1. Sign up at https://deepinfra.com
2. Navigate to API Keys section
3. Generate a new API key
4. Add to `backend/.env`:
   ```env
   DEEPINFRA_API_KEY=your-actual-key-here
   ```

**OpenAI API Key (Optional):**
1. Sign up at https://platform.openai.com
2. Navigate to API Keys section
3. Generate a new API key
4. Add to `backend/.env`:
   ```env
   OPENAI_API_KEY=your-actual-key-here
   ```

### Testing API Endpoints

**Using curl:**
```bash
# Health check
curl http://localhost:8000/health

# Get API documentation
curl http://localhost:8000/openapi.json

# Test discovery flow creation (in demo mode)
curl -X POST http://localhost:8000/api/v1/discovery/flows \
  -H "Content-Type: application/json" \
  -H "X-Client-Account-Id: 11111111-1111-1111-1111-111111111111" \
  -H "X-Engagement-Id: 22222222-2222-2222-2222-222222222222" \
  -d '{"flow_name": "Test Flow", "description": "Test discovery flow"}'
```

**Using Swagger UI:**
1. Open http://localhost:8000/docs
2. Explore available endpoints
3. Use "Try it out" functionality to test APIs
4. Authentication: Use demo headers if needed

## Common Issues and Solutions

### Port Conflicts

**Issue:** Port already in use
```bash
Error: bind: address already in use
```

**Solution:**
```bash
# Check what's using the ports
lsof -i :8000  # Backend
lsof -i :8081  # Frontend
lsof -i :5433  # Database

# Kill processes using the ports
kill -9 $(lsof -t -i:8000)
kill -9 $(lsof -t -i:8081)
kill -9 $(lsof -t -i:5433)

# Or modify ports in docker-compose.yml
```

### Docker Issues

**Issue:** Docker daemon not running
```bash
Error: Cannot connect to the Docker daemon
```

**Solution:**
```bash
# Start Docker service
# macOS: Start Docker Desktop
# Linux:
sudo systemctl start docker
sudo systemctl enable docker

# Windows: Start Docker Desktop
```

**Issue:** Permission denied
```bash
Error: permission denied while trying to connect to Docker daemon
```

**Solution:**
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
# Log out and log back in

# Or use sudo with docker commands temporarily
sudo docker-compose -f config/docker/docker-compose.yml up -d
```

### Database Issues

**Issue:** Database connection failed
```bash
Error: FATAL: password authentication failed
```

**Solution:**
```bash
# Reset database container
docker-compose -f config/docker/docker-compose.yml down postgres
docker volume rm migration_postgres_data
docker-compose -f config/docker/docker-compose.yml up -d postgres

# Wait for database to initialize
docker-compose -f config/docker/docker-compose.yml logs -f postgres
```

**Issue:** Migration errors
```bash
Error: Target database is not up to date
```

**Solution:**
```bash
# Enter backend container and run migrations
docker exec -it migration_backend bash
alembic upgrade head

# If migrations fail, check migration files
ls alembic/versions/
```

### Build Issues

**Issue:** Container build failures
```bash
Error: failed to solve: process "/bin/sh -c pip install -r requirements.txt" did not complete successfully
```

**Solution:**
```bash
# Clean Docker cache
docker system prune -f
docker builder prune -f

# Rebuild without cache
docker-compose -f config/docker/docker-compose.yml build --no-cache
```

**Issue:** Frontend build errors
```bash
Error: Cannot find module 'next'
```

**Solution:**
```bash
# Clear npm cache and rebuild
docker-compose -f config/docker/docker-compose.yml down frontend
docker volume rm migration_frontend_node_modules
docker-compose -f config/docker/docker-compose.yml build --no-cache frontend
docker-compose -f config/docker/docker-compose.yml up -d frontend
```

### Performance Issues

**Issue:** Slow container startup
```bash
# Containers take a long time to start
```

**Solution:**
```bash
# Check available resources
docker system df
free -h  # Linux/macOS
# Task Manager -> Performance (Windows)

# Increase Docker memory allocation (Docker Desktop)
# Preferences -> Resources -> Memory: 8GB+

# Optimize image layers
# Use .dockerignore files to exclude unnecessary files
```

**Issue:** High CPU usage
```bash
# Docker containers using too much CPU
```

**Solution:**
```bash
# Monitor container resource usage
docker stats

# Limit container resources in docker-compose.yml
backend:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
```

## Environment Variations

### Development vs. Production Settings

**Development Environment:**
```env
ENVIRONMENT=development
DEBUG=true
RELOAD=true
LOG_LEVEL=DEBUG
```

**Production Environment:**
```env
ENVIRONMENT=production
DEBUG=false
RELOAD=false
LOG_LEVEL=INFO
```

### Platform-Specific Considerations

**macOS:**
```bash
# Use :cached for better volume performance
volumes:
  - ../../backend:/app:cached
  - ../../frontend:/app:cached
```

**Windows (WSL2):**
```bash
# Ensure files are in WSL2 filesystem for better performance
# Clone repository in WSL2, not Windows filesystem

# Use Linux containers mode in Docker Desktop
```

**Linux:**
```bash
# Standard configuration works best
# Ensure proper user permissions for volume mounts
```

## Advanced Configuration

### Custom Network Configuration

```yaml
# config/docker/docker-compose.override.yml
services:
  backend:
    networks:
      - migration_network
      - external_network

networks:
  migration_network:
    driver: bridge
  external_network:
    external: true
```

### Volume Optimization

```yaml
# Optimized volume configuration
volumes:
  # Use bind mounts for code
  - ../../backend:/app:cached
  
  # Use named volumes for dependencies
  - backend_venv:/app/.venv
  - frontend_node_modules:/app/node_modules
  
  # Use tmpfs for temporary files
  - type: tmpfs
    target: /tmp
    tmpfs:
      size: 100M
```

### Multi-Environment Setup

```bash
# Create environment-specific compose files
cp config/docker/docker-compose.yml config/docker/docker-compose.dev.yml
cp config/docker/docker-compose.yml config/docker/docker-compose.staging.yml

# Use specific environment
docker-compose -f config/docker/docker-compose.dev.yml up -d
```

This comprehensive setup guide ensures a smooth onboarding experience for all developers working on the AI Modernize Migration Platform.