# Docker Rebuild Testing Pattern for Python Code Changes
Date: 2025-11-19
Context: PR #1070 - Bug #10 Testing

## Problem
After committing Python code fixes (Bug #10 deduplication logic), tested without rebuilding Docker containers. Old questionnaire showed 18 duplicates despite new code being committed. This led to false negative - fix appeared not working.

## Root Cause
**Python code changes require container rebuild**, not just restart. Docker containers cache Python bytecode (.pyc files) and module imports. Simply restarting containers (`docker-compose restart`) doesn't reload Python code.

## Solution: Always Rebuild for Python Changes

### Command Pattern
```bash
cd /Users/chocka/CursorProjects/migrate-ui-orchestrator/config/docker

# Stop containers
docker-compose down

# Rebuild and start (REQUIRED for Python changes)
docker-compose up --build -d

# Or single command
docker-compose up --build -d
```

### When Rebuild is REQUIRED
- ✅ Python code changes (.py files)
- ✅ Requirements.txt updates
- ✅ Dockerfile modifications
- ✅ New Python modules added

### When Restart is SUFFICIENT
- ❌ Environment variable changes (.env) - Use `docker-compose restart`
- ❌ Database data changes
- ❌ Frontend code changes (Next.js has hot reload)

## Testing Strategy After Rebuild

### CRITICAL: Test with Fresh Data
**DO NOT test with old data created before fix deployment**

**Problem**: Old questionnaires were created with old code. They won't show fix behavior.

**Solution**: Create NEW questionnaire after Docker rebuild

### Example from PR #1070
```
❌ WRONG Testing Approach:
1. Commit Bug #10 fix
2. Restart Docker containers
3. Test existing questionnaire (created before fix)
4. See 18 duplicates → "Fix doesn't work!"

✅ CORRECT Testing Approach:
1. Commit Bug #10 fix
2. Rebuild Docker containers: docker-compose up --build -d
3. Create FRESH questionnaire
4. See 10 questions → "Fix works!"
```

### Verification Commands
```bash
# 1. Verify Docker containers rebuilt
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
# Look for "Created X seconds ago"

# 2. Verify Python code loaded
docker exec -it migration_backend python -c "
import importlib
import sys
from app.api.v1.endpoints.collection_crud_questionnaires import commands
print(f'Module path: {commands.__file__}')
print(f'Last modified: {importlib.util.find_spec(\"app.api.v1.endpoints.collection_crud_questionnaires.commands\").origin}')
"

# 3. Check backend logs for fix deployment
docker logs migration_backend --tail 50 | grep "Removed.*duplicate questions"
```

## Playwright QA Testing Pattern

When using qa-playwright-tester agent for end-to-end verification:

1. **Rebuild containers first**
2. **Wait for services to be healthy**
3. **Create fresh test data**
4. **Run Playwright tests**

### Example Workflow
```bash
# Rebuild
cd config/docker && docker-compose up --build -d

# Wait for backend health
timeout 60 bash -c 'until docker exec migration_backend curl -f http://localhost:8000/health > /dev/null 2>&1; do sleep 2; done'

# Now test with Playwright
# Agent will create fresh questionnaire
Task tool with subagent_type: "qa-playwright-tester"
```

## Common Mistakes

### Mistake 1: Testing Without Rebuild
```bash
# ❌ WRONG
git commit -m "Fix bug"
docker-compose restart  # Only restarts, doesn't reload Python
# Test shows old behavior
```

### Mistake 2: Testing Old Data
```bash
# ❌ WRONG
docker-compose up --build -d
# Test existing questionnaire created yesterday
# Shows old behavior (data created with old code)
```

### Mistake 3: Partial Rebuild
```bash
# ❌ WRONG
docker-compose build backend  # Only builds, doesn't restart
# Containers still running old code
```

## Correct Pattern
```bash
# ✅ CORRECT COMPLETE WORKFLOW
git add backend/app/api/v1/endpoints/collection_crud_questionnaires/commands.py
git commit -m "fix: Deduplicate questions at flattening stage"

cd config/docker
docker-compose up --build -d  # Rebuild AND restart

# Wait for services
sleep 10

# Create FRESH questionnaire via API or UI
# Test shows NEW behavior
```

## Related Error Patterns

**Error**: "Fix doesn't work, still seeing old behavior"
**Solution**: Rebuild containers, create fresh data

**Error**: "Pre-commit hooks pass but tests fail in Docker"
**Solution**: Rebuild containers to match local environment

**Error**: "Works locally but not in Railway"
**Solution**: Railway auto-rebuilds on push, local needs manual rebuild

## Related Memories
- `docker_command_patterns` - Docker operations
- `testing_docker_workflows` - Testing in Docker
- `qa_playwright_testing_patterns` - Playwright integration
