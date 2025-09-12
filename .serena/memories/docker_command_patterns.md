# Docker Command Patterns for This Project

## Critical Pattern
**All Docker commands must use**: `-f config/docker/docker-compose.yml`

Docker Compose files are in `config/docker/` directory, not project root.

## Common Commands
```bash
# Start services
docker-compose -f config/docker/docker-compose.yml up -d

# Stop services
docker-compose -f config/docker/docker-compose.yml down

# View logs
docker-compose -f config/docker/docker-compose.yml logs -f [service]

# Execute commands in container
docker-compose -f config/docker/docker-compose.yml exec [service] [command]

# Check service status
docker-compose -f config/docker/docker-compose.yml ps
```

## Database Commands
```bash
# Backup database
docker-compose -f config/docker/docker-compose.yml exec postgres pg_dump -U postgres -d migration_db > backup.sql

# Restore database
docker-compose -f config/docker/docker-compose.yml exec -T postgres psql -U postgres -d migration_db < backup.sql

# Run migrations
docker-compose -f config/docker/docker-compose.yml exec backend alembic upgrade head
```

## Environment-Specific Files
- Development: `docker-compose.yml`
- Production: `docker-compose.prod.yml`
- Staging: `docker-compose.staging.yml`
- Secure: `docker-compose.secure.yml`

## Database Credentials
- User: `postgres`
- Database: `migration_db`
- Port: 5433 (external), 5432 (internal)
