# Common Bug Fixes and Solutions

## JSON Serialization Errors

### datetime objects
```python
# ERROR: Object of type datetime is not JSON serializable
# WRONG
return {"timestamp": datetime.utcnow()}

# CORRECT
return {"timestamp": datetime.utcnow().isoformat()}
```

## Progress Calculation Issues

### 0% Initial Progress Bug
```python
# WRONG: Shows 0% for first phase
progress = int((current_index / len(phases)) * 100)

# CORRECT: 1-based calculation
progress = int(((current_index + 1) / len(phases)) * 100)

# Handle completion state
if hasattr(flow_state, "status") and flow_state.status == FlowStatus.COMPLETED:
    return 100
```

## Import Circular Dependencies

### Solution Pattern
```python
# WRONG: Circular import
# file1.py
from .file2 import ClassB
class ClassA: pass

# file2.py
from .file1 import ClassA
class ClassB: pass

# CORRECT: Move shared dependencies
# shared.py
class BaseClass: pass

# file1.py
from .shared import BaseClass
class ClassA(BaseClass): pass

# file2.py
from .shared import BaseClass
from .file1 import ClassA  # Now safe
class ClassB(BaseClass): pass
```

## Undefined Name Errors (F821)

### APITags Import Location
```python
# WRONG: Import inside docstring
"""
from app.api.v1.api_tags import APITags
Module description
"""

# CORRECT: Import after docstring
"""
Module description
"""
from app.api.v1.api_tags import APITags
```

## Multi-line Regex Detection

### Pattern Matching Across Lines
```python
# WRONG: Line-by-line check misses multi-line
for line in lines:
    if "APIRouter" in line and "tags=" in line:
        violations.append(line)

# CORRECT: Regex with MULTILINE and DOTALL
pattern = re.compile(
    r'APIRouter\s*\([^)]*tags\s*=\s*\[[^\]]*\][^)]*\)',
    re.MULTILINE | re.DOTALL
)
for match in pattern.finditer(content):
    line_no = content.count('\n', 0, match.start()) + 1
    violations.append((line_no, match.group(0)))
```

## Error Response Standardization

### Structured Error Format
```python
# WRONG: String error
return {"error": "Service degraded"}

# CORRECT: Structured with code
return {
    "error": {
        "code": "SERVICE_DEGRADED",
        "message": "Service degraded; returning fallback data"
    }
}
```

## File Length Compliance

### Modularization Pattern
```python
# When file exceeds 400 lines, split into:
module_name/
    __init__.py       # Main router/exports
    routes/
        route1.py     # Endpoint handlers
        route2.py
    services/
        service1.py   # Business logic
        service2.py
    models/
        schemas.py    # Pydantic models
        db_models.py  # SQLAlchemy models
```

## Router Registration Missing

### Add to router_imports.py
```python
# Add conditional import
try:
    from app.api.v1.endpoints.new_module import router as new_router
    NEW_MODULE_AVAILABLE = True
except ImportError:
    new_router = None
    NEW_MODULE_AVAILABLE = False
```

### Add to router_registry.py
```python
# In appropriate register function
if NEW_MODULE_AVAILABLE:
    api_router.include_router(new_router, prefix="/new-path")
    logger.info("✅ New module router included")
```

## Quick Validation Commands

```bash
# Check API tags
python scripts/check_api_tags.py --fix

# Run pre-commit on specific files
pre-commit run --files path/to/file.py

# Check file length
find app -name "*.py" -exec wc -l {} + | awk '$1 > 400'

# Test specific endpoint
curl -s http://localhost:8081/api/v1/endpoint | python -m json.tool
```
