# Docker & Deployment Patterns Master

**Last Updated**: 2025-11-30
**Version**: 1.0
**Consolidates**: 15 memories
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **Config Path**: Always use `-f config/docker/docker-compose.yml`
> 2. **Ports**: Frontend=8081, Backend=8000, Postgres=5433
> 3. **No-Cache Rebuild**: Use when Python changes not reflected
> 4. **Override Files**: Remove `docker-compose.override.yml` if conflicting
> 5. **Railway**: No WebSockets, use HTTP polling

---

## Requirements File Mismatch (CRITICAL)

### Railway/Azure Dockerfile Uses Different Requirements File

**Problem**: Local development works but Railway/Azure deployment fails with `ModuleNotFoundError`.

**Root Cause**: Railway Dockerfile uses `config/dependencies/requirements-docker.txt`, NOT `backend/requirements.txt`.

**From root Dockerfile (line 25)**:
```dockerfile
COPY config/dependencies/requirements-docker.txt requirements.txt
```

**Symptom**:
```
Background generation failed for flow ... (exception type: ModuleNotFoundError)
```

**Prevention**: When adding new Python dependencies:
1. Add to `backend/requirements.txt` (local dev)
2. **ALSO add to** `config/dependencies/requirements-docker.txt` (Railway/Azure deployment)

**Related Files**:
- `/Dockerfile` - Railway deployment (uses requirements-docker.txt)
- `/config/docker/Dockerfile.backend` - Local Docker (uses backend/requirements.txt)
- `/backend/requirements.txt` - Local development
- `/config/dependencies/requirements-docker.txt` - Production deployment

---

## Grafana Dashboard Debugging

### Issue: Dashboard Shows "No Data" Despite Working Backend

**Root Cause Pattern**: Default time ranges don't match actual data timestamps.

**Solution**:
```json
// In Grafana dashboard JSON (e.g., llm-costs.json):
"time": {
  "from": "now-30d",  // Was: "now-24h" - too narrow
  "to": "now"
}
```

### Issue: PostgreSQL RLS Blocking Grafana Queries

**Symptom**: PostgreSQL queries return 0 rows for `grafana_readonly` user but full data for `postgres` user.

**Root Cause**: Row Level Security (RLS) is enabled and `grafana_readonly` lacks `BYPASSRLS`.

**Fix**:
```bash
sudo docker exec migration_postgres psql -U postgres -d migration_db -c "ALTER ROLE grafana_readonly BYPASSRLS;"
```

**IMPORTANT**: BYPASSRLS is NOT persistent across container restarts.

### Issue: "origin not allowed" 403 Error

**Root Cause**: Docker Compose variable substitution happens at PARSE TIME, not runtime.

**Fix**: Use `--env-file` flag:
```bash
cd ~/AIForce-Assess/config/docker
sudo docker compose --env-file .env.observability -f docker-compose.observability.yml up -d
```

### Correct Observability Stack Startup (Azure)

```bash
cd ~/AIForce-Assess/config/docker

# Start ALL observability services with correct env file
sudo docker compose --env-file .env.observability -f docker-compose.observability.yml up -d

# Apply BYPASSRLS (required after every PostgreSQL restart)
sudo docker exec migration_postgres psql -U postgres -d migration_db -c "ALTER ROLE grafana_readonly BYPASSRLS;"

# Verify Grafana environment
sudo docker exec migration_grafana printenv | grep GF_SERVER
# Should show Azure domain, NOT localhost
```

---

## Docker Commands

### Essential Commands

```bash
# Start services (from project root)
cd config/docker && docker-compose up -d

# View logs
docker logs migration_backend -f
docker logs migration_frontend -f

# Access containers
docker exec -it migration_backend bash
docker exec -it migration_postgres psql -U postgres -d migration_db

# Restart after code changes
docker restart migration_backend

# Full rebuild (when restart doesn't work)
docker-compose -f config/docker/docker-compose.yml build --no-cache backend
docker-compose -f config/docker/docker-compose.yml up -d
```

### Database Commands

```bash
# Run migrations
docker exec migration_backend alembic upgrade head

# Check database
docker exec -it migration_postgres psql -U postgres -d migration_db

# Backup
docker exec migration_postgres pg_dump -U postgres migration_db > backup.sql
```

---

## Common Issues

### Issue: Python changes not reflected

**Solution**: No-cache rebuild
```bash
docker-compose build --no-cache backend && docker-compose up -d
```

### Issue: PostgreSQL version mismatch

**Cause**: `docker-compose.override.yml` overriding main config

**Solution**: Remove override file or ensure consistency

### Issue: Stale .pyc files

**Solution**: Clean rebuild
```bash
docker exec migration_backend find . -name "*.pyc" -delete
docker restart migration_backend
```

---

## Railway Deployment

**Key Constraints**:
- No WebSockets (use HTTP polling)
- Environment variables via Railway dashboard
- Dockerfile must match requirements.txt

**Polling Pattern**:
```typescript
refetchInterval: status === 'running' ? 5000 : 15000
```

---

## Environment Files

- Development: `docker-compose.yml`
- Production: `docker-compose.prod.yml`
- Staging: `docker-compose.staging.yml`

---

## Consolidated Sources

| Original Memory | Key Contribution |
|-----------------|------------------|
| `docker_command_patterns` | Command reference |
| `docker_no_cache_rebuild_stale_pyc_fix_2025_10` | Stale file fix |
| `railway_deployment_fixes` | Railway patterns |
| `docker_restart_not_rebuild` | When to restart vs rebuild |
| `railway-dockerfile-vs-requirements-dependency-issue-2025-11` | Requirements file mismatch |
| `observability-grafana-dashboard-debugging` | Grafana RLS, time ranges, env files |

**Archive Location**: `.serena/archive/docker/`

---

## Search Keywords

docker, compose, railway, deployment, restart, rebuild, postgres, container, grafana, RLS, BYPASSRLS, env_file, requirements-docker
