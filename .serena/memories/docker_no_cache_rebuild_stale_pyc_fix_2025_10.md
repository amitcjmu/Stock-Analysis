# Docker No-Cache Rebuild for Stale Python Bytecode (Oct 2025)

## Problem
After code changes, Docker rebuild not picking up latest code:
```
ContextAwareRepository.__init__() got an unexpected keyword argument 'client_account_id'
```

Code showed correct signature, but container still using old implementation.

## Root Cause
Docker layer caching preserves `.pyc` (Python bytecode) files from previous builds even after source `.py` files change.

**Standard rebuild** (`docker-compose build`):
- Reuses cached layers where possible
- May not regenerate .pyc files
- Stale bytecode → runtime errors

## Solution: Force Complete Rebuild

```bash
# Stop all containers
docker-compose down

# Build with no cache (forces regeneration of ALL layers including .pyc)
docker-compose build --no-cache backend

# Start containers with fresh code
docker-compose up -d
```

## When to Use --no-cache

### ✅ USE when:
- Getting "unexpected keyword argument" errors after code changes
- Repository/service signature changes not reflected in container
- Suspecting stale bytecode or cached imports
- After major refactoring or method signature changes

### ❌ DON'T USE when:
- Normal development (slow - rebuilds everything)
- Only changing environment variables (use restart)
- Only changing frontend code (frontend has hot reload)

## Faster Alternative: Targeted Rebuild

```bash
# Delete specific container and image
docker-compose down backend
docker image rm migration_backend

# Rebuild just backend
docker-compose build backend
docker-compose up -d backend
```

## Verification
```bash
# Check container start time
docker ps --format "{{.Names}}: {{.Status}}"
# Should show "Up X seconds" with recent timestamp

# Check logs for errors
docker logs migration_backend --tail 50

# Test API endpoint
curl http://localhost:8000/health
```

## Prevention Pattern

### For Development
```bash
# Use volume mounts for hot reload (already configured)
volumes:
  - ./backend:/app

# Python auto-reloads on .py changes
# BUT: Signatures/classes may need container restart
```

### For Signature Changes
```bash
# Quick restart (usually sufficient)
docker-compose restart backend

# If errors persist → full rebuild
docker-compose build --no-cache backend
```

## Related Errors
This pattern fixes:
- `TypeError: __init__() got an unexpected keyword argument`
- `AttributeError: object has no attribute 'method_name'` (after adding method)
- Import errors for recently added modules
- Stale agent pool configurations

## CI/CD Note
Production builds should ALWAYS use `--no-cache` to ensure consistency:
```dockerfile
# Railway/Docker Hub
docker build --no-cache -t app:latest .
```

## Commit Context
- Issue: ContextAwareRepository error persisting after rebuild
- Resolution: `docker-compose build --no-cache backend`
- Time: ~2-3 minutes for full backend rebuild
- Result: Container "Up 13 seconds" with fresh code
