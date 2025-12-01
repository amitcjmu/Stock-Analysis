# Docker Deployment Testing Workflow

## Complete Testing Process for Fresh Deployments

### Prerequisites Check
```bash
# 1. Clean existing environment completely
docker stop $(docker ps -aq -f "name=migration_")
docker rm $(docker ps -aq -f "name=migration_")
docker volume rm $(docker volume ls -q | grep migration)
docker system prune -af --volumes  # Reclaim all space
```

### Build Verification
```bash
# 2. Use docker-start.sh for standardized deployment
./docker-start.sh  # NOT docker-compose directly
```

### Common Build Issues & Fixes

#### Bleach Version Error
**Issue**: `ERROR: No matching distribution found for bleach==6.3.1`
**Fix**: Update requirements.txt to `bleach==6.2.0` (latest available)

#### Docker Compose Target Errors
**Issue**: `target stage "development" could not be found`
**Fix**: Use base docker-compose.yml without dev overrides for fresh builds

### Service Health Verification
```bash
# Backend health
curl http://localhost:8000/health  # Expected: {"status":"healthy"}

# Frontend access
curl -I http://localhost:8081  # Expected: HTTP/1.1 200 OK

# Check logs for startup issues
docker logs migration_backend --tail=50 | grep -E "ERROR|WARNING|Started"
docker logs migration_frontend --tail=20
```

### Test Credentials
- **Working**: `demo@demo-corp.com / Demo123!`
- **Note**: Documentation may show `Password123!` but actual is `Demo123!`

### Expected Services
- Backend: http://localhost:8000 (API docs at /docs)
- Frontend: http://localhost:8081
- PostgreSQL: localhost:5433 (postgres/postgres)
- Redis: localhost:6379

### Validation Checklist
- [ ] All containers running without exits
- [ ] Backend health endpoint responds
- [ ] Frontend login page loads
- [ ] Demo user can authenticate
- [ ] Database migrations complete
- [ ] No critical errors in logs
