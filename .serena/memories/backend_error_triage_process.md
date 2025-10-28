# Backend Error Triage and Fix Process

## Error Analysis Pattern

### 1. Read Error Logs Carefully
```bash
# Get recent backend logs
docker logs migration_backend --tail 100

# Focus on ERROR and WARNING lines
docker logs migration_backend 2>&1 | grep -E "ERROR|WARNING" | tail -50
```

### 2. Identify Root Cause (Not Symptoms)
**Example from Session**:
```
❌ Symptom: "Failed to save phase results: TypeError"
✅ Root Cause: TaskOutput object not serialized before JSONB field
```

### 3. Check ADR Compliance First
Before implementing fix, check if pattern already exists:
- `docs/adr/029-llm-output-json-sanitization-pattern.md` - JSON serialization
- `docs/adr/024-tenant-memory-manager-architecture.md` - Agent memory
- `docs/adr/019-crewai-deepinfra-embeddings-patch.md` - CrewAI integration

### 4. Search for Existing Utilities
```bash
# Find utilities in codebase
find backend/app/utils -name "*.py" | xargs grep -l "sanitize"

# Check if pattern already implemented
grep -r "sanitize_for_json" backend/app
```

## Common Error Patterns

### JSON Serialization Errors
**Error**: `TypeError: Object of type X is not JSON serializable`

**Check**:
1. Is this LLM output? → Use `sanitize_for_json()` per ADR-029
2. Is this datetime? → Convert to ISO string
3. Is this Pydantic model? → Extract dict or specific attributes

### Database Transaction Errors
**Error**: `psycopg.errors.InFailedSqlTransaction`

**Fix Pattern**:
```python
try:
    result = await self.db.execute(stmt)
except Exception as e:
    logger.warning(f"Transaction aborted, rolling back: {e}")
    await self.db.rollback()
    # Retry with clean transaction
    result = await self.db.execute(stmt)
```

### Import Errors in Assessment Executors
**Error**: `ImportError: cannot import name 'TaskOutput'`

**Fix**: Import inside function to avoid circular dependencies
```python
# ✅ Good - inside function
def execute_task():
    from crewai import TaskOutput
    # use TaskOutput

# ❌ Bad - top-level import may cause circular dependency
from crewai import TaskOutput
```

## Verification Steps

### 1. Import Test
```bash
docker exec migration_backend python3.11 -c "
import sys
sys.path.insert(0, '/app/backend')
from app.services.module import ClassName
print('✅ Import successful')
"
```

### 2. Restart Backend
```bash
docker restart migration_backend
sleep 5
docker logs migration_backend --tail 50
```

### 3. Check for Startup Errors
Look for:
- ✅ "initialized successfully"
- ✅ "router registered"
- ❌ "Failed to import"
- ❌ "router not available"

## Pre-commit Hook Handling

### If Pre-commit Fails
```bash
# Black reformatting
# Files were modified by this hook - This is EXPECTED
# Add reformatted files and recommit

git add <reformatted_files>
git commit -m "Same commit message"
```

### Required Checks
All must pass:
- Detect hardcoded secrets ✅
- bandit security ✅
- black formatting ✅
- flake8 linting ✅
- mypy type checking ✅
- Architectural policies ✅

## Fix Documentation

### Commit Message Format
```
fix: [One-line summary]

[Detailed description]

Changes:
- Specific change 1
- Specific change 2

Root Cause:
[Technical explanation]

Impact:
[What was broken, what's fixed]

Compliance:
- ADR-XXX: [Relevant ADR]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Related Files from Session
- TaskOutput fix: 6 assessment executors
- JSON sanitization: `backend/app/utils/json_sanitization.py`
- Phase results: `backend/app/repositories/assessment_flow_repository/commands/flow_commands/phase_results.py`
