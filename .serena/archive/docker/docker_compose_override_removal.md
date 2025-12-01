# Docker Compose Override Removal Pattern [2025-01-18]

## Critical Issue: PostgreSQL Version Downgrade
**Problem**: docker-compose.override.yml silently forcing pg16 instead of pg17
**Root Cause**: Docker automatically loads override files without notification
**Solution**: Remove override file completely
**Code**:
```bash
# Check for override file
ls config/docker/docker-compose.override.yml

# Remove if exists
rm config/docker/docker-compose.override.yml

# Verify main compose uses correct version
grep "pgvector/pgvector" config/docker/docker-compose.yml
# Should show: pgvector/pgvector:pg17
```
**Impact**: Prevents silent PostgreSQL downgrades that break data compatibility

## Merge Conflict Resolution
**Problem**: Override file deleted in feature branch, modified in main
**Solution**: Keep deletion when intentional
**Code**:
```bash
# During merge conflict
git rm config/docker/docker-compose.override.yml
git commit -m "Merge: Keep docker-compose.override.yml deleted"
```
**Rationale**: Override files often cause configuration drift
