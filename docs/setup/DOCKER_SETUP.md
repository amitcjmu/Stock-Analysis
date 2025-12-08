# Docker Setup Guide

## Prerequisites

1. **Docker Desktop** installed and running
   - [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Ensure Docker is running before proceeding

2. **System Requirements**
   - 4GB+ RAM available for Docker
   - 10GB+ free disk space
   - Ports 8000, 8081, 5433, 6379 available

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd migrate-ui-orchestrator

# Start all services
./docker-start.sh

# Access the application
# Frontend: http://localhost:8081
# Backend API: http://localhost:8000/docs
```

## Detailed Setup Instructions

### 1. First Time Setup

The `docker-start.sh` script will automatically:
- Check if Docker is running
- Verify all required files exist
- Create a `.env` file if missing
- Build Docker images
- Start all services
- Validate services are running properly

```bash
# Run the start script
./docker-start.sh
```

### 2. Environment Configuration

If you need to add API keys or modify settings:

```bash
# Edit the environment file
nano backend/.env

# Add your API keys:
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
DEEPINFRA_API_KEY=your-key-here
```

### 3. Service Management

```bash
# Start services
./docker-start.sh

# Stop services
./docker-stop.sh

# Stop and remove volumes (reset database)
./docker-stop.sh --clean-volumes

# Complete cleanup (remove everything)
./docker-stop.sh --clean-all
```

## Service Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:8081 | React application |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| PostgreSQL | localhost:5433 | Database (user: postgres, password: postgres) |
| Redis | localhost:6379 | Cache server |

## Troubleshooting

### Common Issues and Solutions

#### 1. Docker is not running
```bash
# Error: Docker is not running
# Solution: Start Docker Desktop application
```

#### 2. Port already in use
```bash
# Error: bind: address already in use
# Solution: Stop conflicting services or change ports in docker-compose.yml
lsof -i :8000  # Check what's using port 8000
lsof -i :8081  # Check what's using port 8081
lsof -i :5433  # Check what's using port 5433
```

#### 3. PostgreSQL fails to start
```bash
# Solution: Clean up and restart
./docker-stop.sh --clean-volumes
./docker-start.sh
```

#### 4. Out of disk space
```bash
# Clean up Docker resources
docker system prune -af --volumes
# Then restart
./docker-start.sh
```

#### 5. Permission denied errors
```bash
# Make scripts executable
chmod +x docker-start.sh
chmod +x docker-stop.sh
```

## Docker Commands Reference

```bash
# View logs for all services
docker-compose -f config/docker/docker-compose.yml logs -f

# View logs for specific service
docker-compose -f config/docker/docker-compose.yml logs -f backend

# Check service status
docker-compose -f config/docker/docker-compose.yml ps

# Execute commands in containers
docker-compose -f config/docker/docker-compose.yml exec backend bash
docker-compose -f config/docker/docker-compose.yml exec postgres psql -U postgres -d migration_db

# Rebuild images
docker-compose -f config/docker/docker-compose.yml build --no-cache

# Clean everything and start fresh
./docker-stop.sh --clean-all
docker system prune -af --volumes
./docker-start.sh
```

## Project Structure

```
migrate-ui-orchestrator/
├── docker-start.sh          # Start script with validation
├── docker-stop.sh           # Stop script with cleanup options
├── config/
│   └── docker/
│       ├── docker-compose.yml         # Main compose configuration
│       ├── docker-compose.override.yml # Local overrides
│       ├── Dockerfile.backend          # Backend image definition
│       └── Dockerfile.frontend         # Frontend image definition
├── backend/
│   ├── init.sql            # Database initialization
│   └── .env                # Environment variables (created automatically)
└── frontend/
    └── ...                 # React application
```

## Development Workflow

1. **Start services**: `./docker-start.sh`
2. **Make code changes** - changes are reflected immediately
3. **View logs**: `docker-compose -f config/docker/docker-compose.yml logs -f`
4. **Stop when done**: `./docker-stop.sh`

## Database Management

```bash
# Connect to database
docker-compose -f config/docker/docker-compose.yml exec postgres psql -U postgres -d migration_db

# Backup database
docker-compose -f config/docker/docker-compose.yml exec postgres pg_dump -U postgres migration_db > backup.sql

# Restore database
cat backup.sql | docker-compose -f config/docker/docker-compose.yml exec -T postgres psql -U postgres -d migration_db
```

## Support

If you encounter issues not covered here:
1. Check the logs: `docker-compose -f config/docker/docker-compose.yml logs`
2. Ensure all prerequisites are met
3. Try a clean restart: `./docker-stop.sh --clean-all && ./docker-start.sh`
4. Check the project's issue tracker
