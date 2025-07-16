# Docker Volume Issues Troubleshooting Guide

## Common Volume Mounting Errors

### 1. PostgreSQL Volume Mounting Error

**Error Message:**
```
Error response from daemon: failed to populate volume: error while mounting volume '/var/snap/docker/common/var-lib-docker/volumes/aiforce-modernize_postgres_data/_data': failed to mount local volume: mount /home/ubuntu/AIForce-Modernize/postgres-data-volume:/var/snap/docker/common/var-lib-docker/volumes/aiforce-modernize_postgres_data/_data, flags: 0x1000: no such file or directory
```

**Root Cause:**
- The `docker-compose.override.yml` file was configured to bind mount to a non-existent directory
- The volume configuration was trying to mount `${PWD}/postgres-data-volume` which doesn't exist

**Solution:**
1. **Automated Fix (Recommended):**
   ```bash
   chmod +x scripts/fix-postgres-volume.sh
   ./scripts/fix-postgres-volume.sh
   ```

2. **Manual Fix:**
   ```bash
   # Stop all services
   docker-compose down
   
   # Remove problematic volumes
   docker volume rm aiforce-modernize_postgres_data
   docker volume rm migrate-ui-orchestrator_postgres_data
   
   # Clean up Docker system
   docker system prune -f --volumes
   
   # Start services
   docker-compose up -d
   ```

### 2. Frontend NPM Volume Issues

**Error Message:**
```
npm error code ERR_INVALID_ARG_TYPE
npm error The "path" argument must be of type string or an instance of Buffer or URL. Received null
```

**Solution:**
```bash
chmod +x scripts/fix-frontend-npm.sh
./scripts/fix-frontend-npm.sh
```

### 3. Volume Configuration Best Practices

#### ✅ Recommended: Named Volumes
```yaml
services:
  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
    driver: local
```

#### ❌ Avoid: Bind Mounts to Non-existent Directories
```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/postgres-data-volume  # This directory may not exist
```

### 4. Quick Diagnostic Commands

**Check Volume Status:**
```bash
# List all volumes
docker volume ls

# Inspect specific volume
docker volume inspect migrate-ui-orchestrator_postgres_data

# Check container mounts
docker inspect migration_postgres | grep -A 10 "Mounts"
```

**Check Container Status:**
```bash
# List running containers
docker ps

# Check specific container logs
docker-compose logs postgres
docker-compose logs frontend

# Check service status
docker-compose ps
```

### 5. Clean Slate Recovery

If you need to start completely fresh:

```bash
# Stop all services
docker-compose down -v

# Remove all volumes (⚠️ This will delete all data)
docker volume prune -f

# Remove all images
docker system prune -a -f

# Rebuild and start
docker-compose build --no-cache
docker-compose up -d
```

### 6. Data Backup Before Fixes

Always backup your data before applying volume fixes:

```bash
# Backup PostgreSQL data
docker-compose exec postgres pg_dump -U postgres migration_db > backup.sql

# Or use the automated backup in the fix script
./scripts/fix-postgres-volume.sh  # Includes automatic backup
```

### 7. Environment-Specific Issues

**Development Environment:**
- Use named volumes for simplicity
- Enable volume persistence with `docker-compose.override.yml`

**Production Environment:**
- Use external volumes or cloud storage
- Implement proper backup strategies
- Consider using Docker secrets for sensitive data

### 8. Prevention Tips

1. **Always use named volumes** for data persistence
2. **Avoid bind mounts** to non-existent directories
3. **Test volume configurations** in development first
4. **Keep backups** of important data
5. **Use override files** carefully and document changes

## Quick Fix Commands Summary

```bash
# Fix PostgreSQL volume issues
./scripts/fix-postgres-volume.sh

# Fix frontend NPM issues
./scripts/fix-frontend-npm.sh

# Emergency clean slate
docker-compose down -v && docker system prune -a -f && docker-compose up -d
```